# Recovered Milo checkout

Recovery succeeded on 2026-10-03. The original directory had an unborn main with all
source untracked. A real clone was safely created at:

`C:/Users/kitan/Development/Milo/prepared-checkout`

It retains history from main `81f50574507424bf7d504ed04bf6b554d5a894e1` and uses branch
`backend/supabase-agent`. prepare_checkout.ps1 verified upstream backend/doc blob hashes
before overlaying existing implementation. No overlapping upstream changes were present.
Partner-owned ios/, design/ and SPEC.md came from GitHub unchanged. No reset/force-push.
The original directory, venv, SQLite files and ignored secrets remain intact. Completed source
and docs are also synchronized back there; use prepared-checkout for Git operations.

Use the recovered directory for Git commands. Its backend can reuse the original venv:

```powershell
Set-Location C:/Users/kitan/Development/Milo/prepared-checkout/backend
$miloPython = (Resolve-Path ../../backend/.venv/Scripts/python.exe).Path
& $miloPython scripts/verify_offline.py
# Fill the original backend/.env locally; copy only if absent here.
if (-not (Test-Path -LiteralPath .env)) { Copy-Item -LiteralPath ../../backend/.env -Destination .env }
```

Recovery excluded secrets, venvs, caches, reports and SQLite files. The backend workflow
verifies code only and contains no deployment actions. VERIFICATION.md records checks;
TEAM_STATUS.md records remaining live setup. The backend branch is retained after merging.
GitHub's PR/commit pages provide final publication and merge references.

The recovery script remains useful for another unborn checkout. It refuses existing or
outside targets and stops before overlaying changed upstream backend/docs. Do not rerun it
against the existing prepared-checkout.
