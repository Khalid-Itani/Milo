"""Offline Windows HTTP smoke, graceful shutdown and restart on a disposable test database.

SQLite is injected only into this explicit verification process. Production configuration
continues to require Postgres. No hosted database, provider or tunnel is contacted.
"""
import argparse
from contextlib import asynccontextmanager
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
TOKEN = "offline-process-demo-token"


def serve(path, port):
    import uvicorn
    from sqlmodel import Session, SQLModel
    from app.main import app, lifespan
    from app.seed import seed
    from tests.conftest import test_engine

    engine = test_engine(Path(path))
    SQLModel.metadata.create_all(engine)  # explicit temporary verification adapter only
    factory = lambda: Session(engine, expire_on_commit=False)
    seed(factory=factory)
    app.state.session_factory = factory

    @asynccontextmanager
    async def test_lifespan(application):
        try:
            async with lifespan(application):
                yield
        finally:
            engine.dispose()

    app.router.lifespan_context = test_lifespan
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="info"))
    def stop_on_input():
        sys.stdin.readline()
        server.should_exit = True
    threading.Thread(target=stop_on_input, daemon=True).start()
    server.run()


def verify():
    import httpx
    child_env = dict(os.environ)
    child_env.update(DATABASE_URL="", DEMO_API_TOKEN=TOKEN, DEMO_USER_ID="1",
                     ANTHROPIC_API_KEY="", VISUALIZE_SECRET_KEY="",
                     APP_TIMEZONE="America/New_York", PYTHONPATH=str(ROOT))
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    base = f"http://127.0.0.1:{port}"
    headers = {"Authorization": "Bearer " + TOKEN}
    with tempfile.TemporaryDirectory(prefix="milo-offline-") as temp:
        database = str(Path(temp) / "verification.sqlite")
        def start(log):
            process = subprocess.Popen([sys.executable, str(Path(__file__).resolve()),
                                       "--serve", "--database", database, "--port", str(port)],
                                      cwd=ROOT, env=child_env, stdin=subprocess.PIPE,
                                      stdout=log, stderr=log, text=True)
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError("Verification server exited during startup")
                try:
                    if httpx.get(base + "/health", timeout=1).status_code == 200:
                        return process
                except httpx.TransportError:
                    pass
                time.sleep(0.1)
            stop(process)
            raise RuntimeError("Verification server startup timed out")
        def stop(process):
            if process.poll() is None:
                process.stdin.write("stop\n")
                process.stdin.flush()
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    process.terminate()
                    process.wait(timeout=5)
                    raise RuntimeError("Verification server failed graceful shutdown")
            process.stdin.close()
            assert process.returncode == 0
        def get(path):
            response = httpx.get(base + path, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        log_path = Path(temp) / "server.log"
        with log_path.open("w", encoding="utf-8") as log:
            process = start(log)
            try:
                assert httpx.get(base + "/profile", timeout=10).status_code == 401
                assert httpx.get(base + "/openapi.json", timeout=10).json() == json.loads(
                    (ROOT / "openapi.json").read_text(encoding="utf-8"))
                if os.name == "nt":
                    result = subprocess.run(["powershell.exe", "-NoProfile", "-Command",
                        "& ([scriptblock]::Create((Get-Content -LiteralPath scripts/smoke.ps1 -Raw))) "
                        f"-BaseUrl '{base}'"], cwd=ROOT, env=child_env,
                        capture_output=True, text=True, timeout=60)
                    if result.returncode:
                        raise RuntimeError("PowerShell smoke failed: " + result.stderr)
                    print("PASS: real PowerShell smoke.ps1 requests, keyed food replay, sets, Finish and frequency goal.")
                food = {"meal": "breakfast", "name": "Synthetic process restart: eggs and toast",
                        "kcal": 320, "protein_g": 18, "carbs_g": 30, "fat_g": 14,
                        "source": "synthetic", "nutrition_provenance": "synthetic"}
                keyed = headers | {"Idempotency-Key": "offline-process-restart"}
                response = httpx.post(base + "/food", headers=keyed, json=food, timeout=10)
                response.raise_for_status()
                saved = response.json()
                goals, sessions = get("/goals"), get("/sessions")
            finally:
                stop(process)
            process = start(log)
            try:
                assert get("/goals") == goals
                assert get("/sessions") == sessions
                replay = httpx.post(base + "/food", headers=keyed, json=food, timeout=10)
                assert replay.status_code == 200 and replay.json() == saved
                items = [f for meal in get("/food")["meals"].values() for f in meal]
                assert len([f for f in items if f["id"] == saved["id"]]) == 1
                assert get("/today")["kcal"]["eaten"] == sum(f["kcal"] for f in items)
            finally:
                stop(process)
        log_text = log_path.read_text(encoding="utf-8")
        assert log_text.count("Application startup complete") == 2
        assert log_text.count("Application shutdown complete") == 2
    print("PASS: real uvicorn startup/shutdown twice; food, goals, sessions and retry result survived a process restart.")
    print("SQLite was an explicit disposable offline adapter. Supabase persistence and a live HTTPS tunnel were not tested.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--database")
    parser.add_argument("--port", type=int)
    args = parser.parse_args()
    if args.serve:
        serve(args.database, args.port)
    else:
        verify()
