"""Run actual offline checks without installing or making hosted calls/schema changes.

From backend: .venv/Scripts/python.exe scripts/verify_offline.py
Ignored reports retain actual stdout/stderr and exit codes for the handoff.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "verification-results"


def main():
    REPORTS.mkdir(exist_ok=True)
    # Do not forward real credentials to offline verification subprocesses.
    child_env = dict(os.environ)
    child_env.update(DATABASE_URL="", ANTHROPIC_API_KEY="", VISUALIZE_SECRET_KEY="",
                     DEMO_API_TOKEN="offline-demo-token", DEMO_USER_ID="1",
                     APP_TIMEZONE="America/New_York", PYTHONPATH=str(ROOT))
    checks = []
    for name, args in (
        ("runtime-openapi", ["scripts/export_openapi.py"]),
        ("stdlib", ["-m", "unittest", "discover", "-s", "offline_tests", "-v"]),
        ("pytest", ["-m", "pytest", "-q"]),
        ("process-smoke", ["scripts/verify_process.py"]),
    ):
        print(f"Running {name}...", flush=True)
        result = subprocess.run([sys.executable, *args], cwd=ROOT, env=child_env,
                                capture_output=True, text=True, encoding="utf-8", errors="replace")
        (REPORTS / f"{name}.log").write_text(result.stdout + result.stderr, encoding="utf-8")
        checks.append({"check": name, "exit_code": result.returncode,
                       "status": "passed" if result.returncode == 0 else "failed"})
        if name == "runtime-openapi" and result.returncode == 0:
            document = json.loads(result.stdout)
            if "openapi" not in document or "paths" not in document:
                raise ValueError("Invalid runtime OpenAPI output")
            (ROOT / "openapi.json").write_text(json.dumps(document, indent=2, sort_keys=True) + "\n",
                                               encoding="utf-8", newline="\n")
        print(f"{name}: {checks[-1]['status']} (exit {result.returncode})", flush=True)
        if result.returncode:
            print(f"See verification-results/{name}.log", flush=True)
    summary = {"recorded_at": datetime.now(timezone.utc).isoformat(),
               "python": sys.version, "checks": checks,
               "live_checks": "not run; this runner is offline only"}
    (REPORTS / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return 0 if all(c["exit_code"] == 0 for c in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
