# Milo team handoff

Recorded 2026-10-03. Backend source and offline checks are ready; live app/phone testing
still needs the setup below. Working branch: backend/supabase-agent in prepared-checkout.
GitHub's PR/check state records publication and merging. No deployment was performed.

## Backend delivered and verified

- Retained FastAPI/Pydantic/SQLModel/psycopg and the Anthropic SDK tool loop.
- Fixed-owner/demo bearer access; TLS Postgres; reviewed Alembic schema actually applied
  to confirmed project toemuooqjrqfincmzywr. All 15 tables have RLS and no effective client
  table/column/sequence access. Advisors have no ERROR/WARN; expected INFO is documented.
- Shared Today/Train/Eat/Goals records, BMI, timezone/DST totals, preserved targets,
  plans versus consumed food, dated repeat sessions and historical sets.
- Bounded validated tools, transactions, durable keys/effect journals/leases, crash recovery,
  proposals/apply and version history. Read tools refresh after writes. get_today never
  sends scans to Claude; scan context requires separate AI-sharing consent.
- Active sessions remain reachable during plan revision; Finish precedes replacement apply.
- Fresh Visualize session boundary with sanitized failures; consent/dedup summary ingestion.
  Live provider/SDK checks remain separate from HTTP mocks.
- 50 pytest tests, eight stdlib checks, runtime OpenAPI/fixtures, actual Windows PowerShell
  smoke and uvicorn shutdown/restart persistence on a disposable offline database.
  CI covers Linux/3.12 and Windows/3.14 without hosted calls or deployment.

The live backend-to-Supabase check also passed: TLS, current migration, rerunnable seed,
write/read/reconnect and actual process restart with stable keyed replay. Verification
records are labeled synthetic and retained; no provider calls occurred.

## You: remaining backend setup

1. DATABASE_URL is now configured locally and verified. Direct Connect works with TLS on
   this machine; keep the existing ignored file. Revision 0001_milo is applied and the
   seed/write/read/restart check passed. No further database setup is required for this demo.
2. Add Claude/Visualize server keys when available; run each live_providers.py check separately.
   Claude checks tool behavior with two bounded paid calls. Confirm Visualize's session
   contract against the partner's account docs; the public SDK reference was unavailable.
3. Start the documented HTTPS tunnel,
   verify /health and authenticated /profile, and privately share URL/demo token.
   Keep backend/tunnel running for phone checks; rotate demo token afterward.

## Teammate: iOS, SDK and real device

Swift models/client/views were read for compatibility and remain unchanged.

1. Pull merged main or fetch the backend branch. Configure HTTPS URL, disable mocks,
   and send Authorization: Bearer <demo token> on business requests.
2. Retain one action Idempotency-Key through retries. Use current session/set IDs after
   repeat Start. Increase chat timeout to about 300 seconds or safely retry the same key.
3. Handle profile_incomplete, saved targets/preferences/allergies/equipment/timezone,
   and separate default-off storage/AI scan consents.
4. Install Visualize SDK, mint fresh /visualize/session tokens, confirm actual ScanResult
   fields/units, and upload selected consented summaries with stable client_scan_id.
   Verify Bundle/Team settings, camera and TrueDepth on a real iPhone.
5. Refresh Today/goals after Finish and food writes; affected tabs after chat. Add models
   for diet-plans/cards/scans when enabling those UIs. Optional proposal Save calls apply;
   otherwise default immediate save remains compatible.
6. Replace hardcoded dinner suggestions and template PREVIOUS labels when showing real
   data. HTTPS requires no broad iOS transport exception.

No server database/provider secrets belong in Swift or Git. IOS_HANDOFF.md has exact
payloads/refresh rules. Run the five shared stories on the real app after setup;
offline/mocked tests and hosted schema checks do not constitute a physical scan.
