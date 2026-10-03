"""Opt-in live Supabase migration/seed/write/read/process-restart verification.

Requires the explicitly confirmed project reference. Synthetic verification records remain
for inspection. No provider calls, data deletion, reset or tunnel is performed.
"""
import argparse
import os
from pathlib import Path
import socket
import subprocess
import sys
import threading
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def serve(port):
    import uvicorn
    from app.main import app
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="info"))
    def stop_on_input():
        sys.stdin.readline()
        server.should_exit = True
    threading.Thread(target=stop_on_input, daemon=True).start()
    server.run()


def check(project_ref):
    import httpx
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import func, text
    from sqlalchemy.engine import make_url
    from sqlmodel import Session, select
    from app.config import settings
    from app.db import get_engine, close_engine
    from app.seed import seed
    from app import services as svc
    from app.models import (WorkoutPlan, Workout, Exercise, WorkoutSession, WorkoutSet,
                            FoodLog, DietPlan, Goal, ChatMessage, Proposal, Scan, Mutation, ToolEffect)
    from scripts.check_database import check as check_database

    url = make_url(settings.database_url)
    assert url.host == f"db.{project_ref}.supabase.co" or (
        url.host and url.host.endswith(".pooler.supabase.com") and
        url.username and url.username.endswith("." + project_ref)), "Connection project mismatch"
    assert settings.demo_api_token, "Demo token missing"
    with get_engine().connect() as connection:
        assert connection.execute(text("SELECT version_num FROM public.alembic_version")).scalar_one() == "0001_milo"
    print("PASS: confirmed project TLS psycopg connection and remote Alembic revision.", flush=True)
    command.upgrade(Config(str(ROOT / "alembic.ini")), "head")
    print("PASS: Alembic upgrade head is already current.", flush=True)
    seed()
    def snapshot():
        with Session(get_engine()) as session:
            models = (WorkoutPlan, Workout, Exercise, WorkoutSession, WorkoutSet, FoodLog,
                      DietPlan, Goal, ChatMessage, Proposal, Scan, Mutation, ToolEffect)
            counts = [session.exec(select(func.count()).select_from(m).where(
                m.owner_id == settings.demo_user_id)).one() for m in models]
            return svc.public(svc.profile(session, required=True)), counts
    first = snapshot()
    seed()
    assert snapshot() == first
    print("PASS: explicit synthetic seed rerun preserves profile and all owner row counts.", flush=True)
    check_database()
    close_engine()
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    headers = {"Authorization": "Bearer " + settings.demo_api_token}
    reports = ROOT / "verification-results"
    reports.mkdir(exist_ok=True)
    def stop(process):
        if process.poll() is None:
            process.stdin.write("stop\n")
            process.stdin.flush()
            try:
                process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                process.terminate()
                process.wait(timeout=5)
                raise RuntimeError("Backend did not shut down gracefully")
        process.stdin.close()
        assert process.returncode == 0
    def start(log):
        process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "--serve", "--port", str(port)],
            cwd=ROOT, env=os.environ.copy(), stdin=subprocess.PIPE, stdout=log, stderr=log, text=True)
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError("Backend exited during startup")
            try:
                if httpx.get(base + "/health", timeout=1).status_code == 200:
                    return process
            except httpx.TransportError:
                pass
            time.sleep(0.1)
        stop(process)
        raise RuntimeError("Backend startup timed out")
    def get(path):
        response = httpx.get(base + path, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    with (reports / "live-process-server.log").open("w", encoding="utf-8") as log:
        process = start(log)
        try:
            assert httpx.get(base + "/profile", timeout=10).status_code == 401
            profile = get("/profile")
            body = {"meal": "breakfast", "name": "Synthetic live persistence: eggs and toast",
                    "kcal": 320, "protein_g": 18, "carbs_g": 30, "fat_g": 14,
                    "source": "synthetic", "nutrition_provenance": "synthetic"}
            keyed = headers | {"Idempotency-Key": "live-verification:" + str(uuid4())}
            response = httpx.post(base + "/food", headers=keyed, json=body, timeout=30)
            response.raise_for_status()
            saved = response.json()
            goals, sessions, history, cards = (get(p) for p in ("/goals", "/sessions", "/chat/history", "/cards"))
        finally:
            stop(process)
        process = start(log)
        try:
            assert get("/profile") == profile
            assert get("/goals") == goals and get("/sessions") == sessions
            assert get("/chat/history") == history and get("/cards") == cards
            response = httpx.post(base + "/food", headers=keyed, json=body, timeout=30)
            response.raise_for_status()
            assert response.json() == saved
            items = [item for meal in get("/food")["meals"].values() for item in meal]
            assert len([item for item in items if item["id"] == saved["id"]]) == 1
            assert get("/today")["kcal"]["eaten"] == round(sum(item["kcal"] for item in items))
        finally:
            stop(process)
    print("PASS: live Postgres API write/read, keyed replay, and two actual backend process lifecycles.")
    print("Synthetic food ID", saved["id"], "retained; tokens, connection string and provider keys withheld.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-ref")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--port", type=int)
    args = parser.parse_args()
    if args.serve:
        serve(args.port)
    else:
        if not args.project_ref:
            parser.error("--project-ref must be explicitly confirmed")
        try:
            check(args.project_ref)
        except Exception as exc:
            # Classify connection failures without dumping DSNs, parameters or raw exceptions.
            reason = str(getattr(exc, "orig", exc)).lower()
            category = next((label for phrase, label in (
                ("network is unreachable", "network_unreachable"),
                ("could not translate host", "dns_unavailable"),
                ("getaddrinfo", "dns_unavailable"),
                ("password authentication", "database_password_rejected"),
                ("timeout", "connection_timeout"),
                ("timed out", "connection_timeout"),
                ("project mismatch", "project_mismatch")) if phrase in reason), type(exc).__name__)
            raise SystemExit("Live database verification failed: " + category + "; secret details withheld.") from None
