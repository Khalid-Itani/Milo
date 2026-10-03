# Milo backend

FastAPI + SQLModel/SQLAlchemy + Supabase Postgres + the existing Anthropic tool loop.
The phone uses FastAPI, never Supabase directly. No normal-operation SQLite or fake-provider fallback.

## Windows setup (PowerShell, Python 3.12 recommended; 3.11+)

For a new checkout:

```powershell
git clone https://github.com/Khalid-Itani/Milo.git
Set-Location Milo
git switch -c backend/supabase-agent
code .
```

For an existing checkout, inspect `git status --short` and branch first; preserve unrelated changes.
Recovery succeeded into `prepared-checkout` on backend/supabase-agent, preserving history
and partner files. [GIT_RECOVERY.md](../GIT_RECOVERY.md) gives this machine's commands using
the original installed venv. Secrets/venv/SQLite files remain in the original workspace.

```powershell
Set-Location backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path -LiteralPath .env)) { Copy-Item -LiteralPath .env.example -Destination .env }
notepad .env
# Generate a temporary token locally if needed; place it in DEMO_API_TOKEN in .env.
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(32))"
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m app.seed
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Use a real installed Python executable in place of py if the Windows Store alias is not working.
All commands after venv creation use its python.exe directly, with no activation, admin rights,
execution-policy change, Docker, WSL, macOS or Xcode dependency.
A local ignored .env has a random demo token and a verified Supabase DATABASE_URL; provider keys remain blank.
Do not overwrite an existing credential file. Never paste account secrets into chat.

## Connection, configuration and migrations

In the exact hackathon Supabase project's Connect dialog, copy Session pooler for IPv4 Windows
or direct connection if IPv6 works. Do not infer a host/project from another project, create a new
database or buy an IPv4 add-on. Change only the scheme to postgresql+psycopg, percent-encode reserved
password characters, and include sslmode=require (or verify-full with the appropriate trusted
certificate). Supabase's official connection documentation supports session pooling for persistent
IPv4 backends: [Connect to Postgres](https://supabase.com/docs/guides/database/connecting-to-postgres).
The supported Windows driver is [Psycopg binary](https://www.psycopg.org/psycopg3/docs/basic/install.html),
through [SQLAlchemy's psycopg dialect](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.psycopg).
Pool size is 3 with at most 2 overflow connections and connection timeouts. URLs are never logged.
No Supabase API key is used or required. Local .db files are neither read nor transferred.

Required for operation: DATABASE_URL and DEMO_API_TOKEN. Claude additionally needs ANTHROPIC_API_KEY;
Visualize additionally needs VISUALIZE_SECRET_KEY. ANTHROPIC_MODEL defaults to claude-sonnet-5-5,
with COACH_MODEL as a compatibility alias if the former is unset. This model ID and the standard
Messages/tool-result interface were checked against [Anthropic model docs](https://platform.claude.com/docs/en/models/overview)
and [tool-call docs](https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls).
Default Visualize base URL is https://api.visualizeme.ai; only explicitly configure a pilot override.
DEMO_USER_ID defaults 1; VISUALIZE_HOST_USER_REF defaults milo_demo_1 and remains stable across scans.
APP_TIMEZONE defaults America/New_York; tzdata supplies IANA zones on Windows.

The Alembic initial migration is explicit and transactional, never create_all/drop_all on import.
It enables RLS on all Milo tables and alembic_version, revokes PUBLIC/anon/authenticated table and
sequence access, and creates no public functions, allow-all policies or views. The privileged
backend role may bypass RLS, so every service read/write is scoped to DEMO_USER_ID.
The initial schema was applied to confirmed project toemuooqjrqfincmzywr via reviewed Alembic
SQL through the connected Supabase app; remote Alembic revision is 0001_milo. All 15 tables
have RLS and no client grants. Advisors returned only expected INFO notices. See
[VERIFICATION.md](../VERIFICATION.md) and [migration instructions](migrations/README.md).
The live backend seed/write/read/restart check also passed using the configured TLS URL.

Seeding is explicit: app.seed inserts synthetic records with stable seed_key identifiers.
Repeated runs preserve existing records/profile edits and never duplicate the identified seed.
Food/session source labels and demo names make synthetic data visible. Demo seed dates are anchored
on first insertion; reruns do not manufacture a new day's food. `--fresh` now creates an empty
profile only if absent; it does not delete any existing data. Start without seed if desired:
GET /profile is empty, POST /profile initializes the fixed owner, then use the real workflows.

## Verification and smoke requests

```powershell
# Entire isolated API/domain/provider-mock suite; no hosted credentials or paid calls.
.\.venv\Scripts\python.exe -m pytest -q
# Runtime OpenAPI + stdlib + full pytest + process/PowerShell smoke (ignored reports).
.\.venv\Scripts\python.exe scripts/verify_offline.py
# A smaller separate suite also works with no third-party dependencies installed.
.\.venv\Scripts\python.exe -m unittest discover -s offline_tests -v
# Live DB write/read/reconnect + RLS/grant checks (explicit synthetic verification goal retained).
.\.venv\Scripts\python.exe scripts/check_database.py
# Opt-in exact-project live API write/read and actual backend process restart.
.\.venv\Scripts\python.exe scripts/verify_live_database.py --project-ref toemuooqjrqfincmzywr
# Opt-in live provider checks, separately from pytest (Claude can incur charges).
.\.venv\Scripts\python.exe scripts/live_providers.py claude
.\.venv\Scripts\python.exe scripts/live_providers.py visualize
# Actual runtime OpenAPI, no DB/provider connections.
.\.venv\Scripts\python.exe scripts/export_openapi.py | Set-Content -Encoding utf8 openapi.json
```

Restart uvicorn after a saved write and GET /food, /chat/history, /goals, /sessions and /cards to
verify independent process persistence. check_database.py disposes all connections before reading;
it does not by itself claim that an actual process restart was tested.

For manual API smoke testing in a second terminal:

```powershell
$apiBase = "http://127.0.0.1:8000"
$env:DEMO_API_TOKEN = Read-Host "Enter the temporary demo token from your local .env"
$demoHeaders = @{ Authorization = "Bearer $env:DEMO_API_TOKEN"; "Idempotency-Key" = [guid]::NewGuid().ToString() }
Invoke-RestMethod "$apiBase/health"
Invoke-RestMethod "$apiBase/today" -Headers $demoHeaders
$mealBody = @{ meal="breakfast"; name="Two eggs and toast"; quantity="2 eggs, 2 slices"; kcal=320; protein_g=18; carbs_g=30; fat_g=14 } | ConvertTo-Json
Invoke-RestMethod "$apiBase/food" -Method Post -Headers $demoHeaders -ContentType "application/json" -Body $mealBody
# Retry using the exact same key/body: returns the same FoodLog ID.
Invoke-RestMethod "$apiBase/food" -Method Post -Headers $demoHeaders -ContentType "application/json" -Body $mealBody
Invoke-RestMethod "$apiBase/food" -Headers $demoHeaders
```

scripts/smoke.ps1 covers keyed food replay, set completion, session history, goals and optional live
chat/proposal stories. Read and run/paste it locally; its writes remain as labeled synthetic demo data.
Its IncludeClaude switch explicitly opts into paid Claude calls. Tests cover all five acceptance
stories with provider mocks and also failure, consent, concurrency and crash recovery.
See [actual verification status](../VERIFICATION.md): 50 pytest tests and the full offline
runner passed, including actual PowerShell requests and a disposable SQLite process restart.
Provider results in pytest are mocks; the separate live Supabase persistence check also passed.

## HTTPS tunnel for the real iPhone

Download the Windows executable from [Cloudflare's official downloads](https://developers.cloudflare.com/tunnel/downloads/)
into a local tools directory (no service installation or admin rights needed). In a second terminal,
with uvicorn listening at 127.0.0.1:8000:

```powershell
.\tools\cloudflared.exe tunnel --url http://127.0.0.1:8000
# Replace with the HTTPS URL cloudflared prints:
$httpsBase = "https://YOUR-TEMPORARY-NAME.trycloudflare.com"
Invoke-RestMethod "$httpsBase/health"
Invoke-RestMethod "$httpsBase/profile" -Headers @{ Authorization = "Bearer $env:DEMO_API_TOKEN" }
```

This command is verified against [Quick Tunnel documentation](https://developers.cloudflare.com/tunnel/get-started/quick-tunnels/).
A live tunnel passed HTTPS health and authenticated Supabase profile read here. Its temporary
URL/demo token stay outside Git. The URL changes each launch; both tunnel/server must keep running.
Use the HTTPS URL in the phone's configurable base URL; no broad iOS security exception is required.
Do not enable interactive email protection on this API tunnel: URLSession is a non-interactive client.
Quick Tunnels are temporary development access with no uptime guarantee.

## Handoff and eventual hosting

[API contract](../API_CONTRACT.md), [iOS handoff](../IOS_HANDOFF.md), [fixtures](fixtures/README.md),
and [OpenAPI](openapi.json) document the boundary. The checked-in schema is the actual runtime
FastAPI export; verification checks runtime equality and fixture models. The current APIClient
must add Authorization and stable
mutation retry keys; scan/proposal integration belongs to the Mac partner. No iOS edits were made.

Dockerfile is optional for eventual hosting: inject server env through the host's secret store,
apply migrations as an explicit release step, and run the supplied uvicorn CMD on port 8000.
Never bake .env into the image; .dockerignore excludes it. Nothing was deployed or purchased.
