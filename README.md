# Milo

A chat-first fitness coach: Claude saves workout/diet plans, logs food and actual exercise sets,
and manages goals. Today, Train, Eat and Goals read the same persisted records.

```
backend/   FastAPI + Supabase Postgres + Claude agent (backend/agent/)
ios/       Partner-owned SwiftUI app (existing FitCoach names retained)
design/    Reference-only mockups
```

SPEC.md preserves the original design and successful wire shapes. The current backend behavior
is documented in [API_CONTRACT.md](API_CONTRACT.md); its Postgres, access, consent, BMI and safe-seed
rules supersede the older spec's SQLite/no-auth/guessed-Visualize/destructive-seed instructions.

## 1. Backend (Windows PowerShell)

```powershell
Set-Location backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
if (-not (Test-Path -LiteralPath .env)) { Copy-Item -LiteralPath .env.example -Destination .env }
notepad .env
# Set the exact Supabase TLS DATABASE_URL, temporary demo token and server provider keys locally.
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m app.seed
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

[backend/README.md](backend/README.md) includes connection setup, explicit migrations,
no-activation commands, smoke examples and HTTPS tunnel instructions. No schema/seed runs at
import/startup. Git history was recovered safely into `prepared-checkout`; the original
workspace, secrets and venv remain intact. [GIT_RECOVERY.md](GIT_RECOVERY.md) has this
machine's exact commands. No deployment was performed.

## 2. iOS

```bash
brew install xcodegen
cd ios && xcodegen && open FitCoach.xcodeproj
```

Run on an iPhone simulator. For a real device, set `Config.baseURL` to your Mac's LAN IP. To run without a backend, set `Config.useMock = true`. See `ios/README.md`.


The partner-owned instructions above are retained. For the upgraded Windows-backed API, use
[IOS_HANDOFF.md](IOS_HANDOFF.md): an HTTPS URL and demo Authorization header are required.
The default chat Save behavior still persists plans immediately. Optional proposal mode needs
the partner's apply-button integration.

## 3. Verification and demo

[VERIFICATION.md](VERIFICATION.md) records actual results, including blocked checks.
[TEAM_STATUS.md](TEAM_STATUS.md) separates verified backend work from remaining live setup
and your partner's iOS integrations. All 50 pytest tests, eight dependency-free checks,
runtime schema/fixtures, actual Windows PowerShell smoke, and uvicorn startup/shutdown/restart
passed offline. CI runs verification only, without credentials or deployment.

The schema was applied to your confirmed Milo Supabase project; all 15 tables use RLS and
deny client access. The local Connect-dialog DATABASE_URL is configured, and the actual
Supabase seed/write/read/backend-restart checks passed. Claude/Visualize keys and real-phone
checks remain external setup. No physical scan was claimed.

The offline suite covers three-day dumbbell plans, vegetarian plans without consumed calories,
keyed eggs/toast logging, bench sets in repeat sessions, and frequency goals from completed
sessions. Additional tests cover access, ownership, proposals, failure handling, retry concurrency,
scan consent/deduplication, Visualize request/errors, and safe seeding.

[Fixtures](backend/fixtures/README.md) validate against the actual runtime
[OpenAPI](backend/openapi.json) and response models and support partner decoder review.
The existing Eat dinner suggestion and Train previous-target presentation remain partner-owned.
