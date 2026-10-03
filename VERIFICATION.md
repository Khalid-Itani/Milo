# Actual verification status

Recorded 2026-10-03, Windows, Python 3.14.3. Working checkout:
`C:/Users/kitan/Development/Milo/prepared-checkout`, branch `backend/supabase-agent`.
The original workspace, venv, ignored credentials and SQLite files were preserved.

## Passed

- Real Git clone/recovery from main `81f50574507424bf7d504ed04bf6b554d5a894e1`.
  Upstream overlaps checked before copying; no ios/, design/ or SPEC.md edits.
- All twelve pinned requirements installed; pip check reports no broken requirements.
- Full pytest: 50 tests. Isolated SQLite adapter and mocked providers; no hosted/paid calls.
  All five stories exercised: dumbbell save/propose/apply, vegetarian plan without consumed
  calories, one keyed eggs/toast log, repeated bench sessions with preserved sets, and
  frequency goals based on dated completed sessions.
- Eight separate stdlib checks, Python compilation and PowerShell parser checks.
- Real FastAPI OpenAPI export; checked-in JSON equals app.openapi(). Fixtures validate
  against runtime models/schema; legacy Swift card data fields checked.
- Real uvicorn HTTP startup, authenticated requests, graceful shutdown and restart twice
  on a disposable offline database. Food, goals, sessions and keyed responses survived.
  This is not a Supabase process persistence check.
- Actual Windows PowerShell smoke.ps1 requests: keyed replay, Start, set update, Finish,
  session history and frequency goal. Fixed top-level JSON array enumeration in the script.
- Mocked recovery-script safety/exclusion checks, plus actual clone/branch recovery above.
- Regression coverage for read tools observing intervening writes, scan privacy in get_today,
  conversation isolation, active-plan replacement and disposal of cached pools at shutdown.

## Live Supabase schema verified

The user confirmed `toemuooqjrqfincmzywr` (Milo, us-east-1). Only this project was inspected.
It was ACTIVE_HEALTHY on Postgres 17.11, with an empty public schema. Generated/reviewed
`alembic upgrade head --sql`; applied through Supabase MCP migration
`20261003143155_milo_alembic_0001`. The SQL includes Alembic version tracking at `0001_milo`.
Do not stamp or recreate the initial schema separately.

Live SQL confirmed 15 tables, RLS on all 15, and zero effective anon/authenticated table,
column or sequence privileges. No data dropped or imported. Security/performance advisors
ran before and after migration and returned no ERROR/WARN findings. Expected INFO findings:

- 15 [RLS enabled without policies](https://supabase.com/docs/guides/database/database-linter?lint=0008_rls_enabled_no_policy):
  intentional deny-by-default client access; privileged backend services enforce ownership.
  Adding client policies would broaden access against the intended architecture.
- 25 [unused indexes](https://supabase.com/docs/guides/database/database-linter?lint=0005_unused_index):
  a new schema with no workload. Keep ownership/FK/date indexes; assess after actual usage.

Reviewed current [connections](https://supabase.com/docs/guides/database/connecting-to-postgres),
[RLS](https://supabase.com/docs/guides/database/postgres/row-level-security),
[Psycopg installation](https://www.psycopg.org/psycopg3/docs/basic/install.html) and
[SQLAlchemy's dialect](https://docs.sqlalchemy.org/en/20/dialects/postgresql.html#module-sqlalchemy.dialects.postgresql.psycopg).
The latest relevant Postgres changelog concerns extensions/operators absent from Milo's schema.

## Live backend persistence passed

The user filled the local DATABASE_URL. Its host matches the confirmed project; normalized
only its driver scheme/TLS query and password URL encoding, without printing the value.
The exact direct Connect-dialog host worked from Windows, so a session pooler was unnecessary.

`scripts/verify_live_database.py --project-ref toemuooqjrqfincmzywr` actually passed:
TLS psycopg connection, Alembic current/no-op upgrade, explicit synthetic seed twice with
unchanged profile/owner row counts, a synthetic goal write/read across reconnect, effective
RLS/grant checks, and two real production-backend startup/shutdown cycles. A keyed food
write survived restart and returned the same FoodLog ID; profile/goals/sessions/history/cards
also persisted. Synthetic verification goal 5 and food 9 remain for inspection. No providers
were called. Runtime secrets are present only in ignored .env files. Add future provider keys
to the running checkout's prepared-checkout/backend/.env and restart the backend after edits.

## Not run / external setup

| Check | Reason / next action |
|---|---|
| Live Claude model/tool round trip | ANTHROPIC_API_KEY blank; live_providers.py claude makes two bounded paid calls when configured |
| Live Visualize session | VISUALIZE_SECRET_KEY blank; request/error behavior tested with HTTP mocks only |
| SDK ScanResult mapping / physical scan | Partner-owned Mac/real-iPhone work, never claimed on Windows |
| Deployment | Not requested or performed; workflow only verifies offline code |

Public Visualize pages did not provide a verifiable SDK/session reference in this review.
The existing configured /v1/sessions + host_user_ref contract has mock coverage; confirm it
with the partner's account/SDK documentation and a real session before demo. Claude Sonnet
5.5's model ID was verified in [official model docs](https://platform.claude.com/docs/en/models/overview);
account availability remains an unrun live check.

## HTTPS and publication

Downloaded cloudflared 2026.9.3 from Cloudflare's official GitHub release to ignored
backend/tools/cloudflared.exe. Started a real Quick Tunnel to the running Supabase-backed
uvicorn server. HTTPS /health returned ok; unauthenticated /profile returned 401;
an authenticated HTTPS /profile read returned the fixed owner's persisted profile.
The temporary URL/demo token remain outside Git and can be shared privately.
No physical phone access or scan was claimed. A Quick Tunnel is temporary dev access;
no hosted application deployment or Cloudflare account purchase was performed.

Branch backend/supabase-agent was pushed normally. [PR #1](https://github.com/Khalid-Itani/Milo/pull/1)
records checks and the merge outcome. GitHub connector PR creation returned 403;
the existing authenticated Git Credential Manager identity successfully created it via the
GitHub REST API. Credentials were held only in memory and never printed or written.

One third-party Starlette/AnyIO deprecation warning is nonfatal. Ignored logs/summary.json
in backend/verification-results retain local evidence. GitHub CI runs Linux/Python 3.12
and Windows/Python 3.14 without credentials, hosted calls or deployment. GitHub's PR/check
state records the publication/merge outcome.

## Exact commands in this recovered checkout

```powershell
Set-Location C:/Users/kitan/Development/Milo/prepared-checkout/backend
$miloPython = (Resolve-Path ../../backend/.venv/Scripts/python.exe).Path
& $miloPython scripts/verify_offline.py
# Fill the original backend/.env locally, then copy only if absent here:
if (-not (Test-Path -LiteralPath .env)) { Copy-Item -LiteralPath ../../backend/.env -Destination .env }
& $miloPython -m alembic current
& $miloPython -m alembic upgrade head
& $miloPython -m app.seed
& $miloPython scripts/check_database.py
& $miloPython scripts/verify_live_database.py --project-ref toemuooqjrqfincmzywr
& $miloPython -m uvicorn app.main:app --host 127.0.0.1 --port 8000
# Restart after a saved API write; read the same ID and retry the same action key.
# Separate opt-in checks:
& $miloPython scripts/live_providers.py claude
& $miloPython scripts/live_providers.py visualize
```

DATABASE_URL is a Postgres URI, not the Dashboard/API URL. Use the confirmed project's
Session pooler host/port, postgresql+psycopg scheme, URL-encoded database password and TLS.
Only HTTPS API URL/demo token/SDK publishable key belong in private mobile configuration.
