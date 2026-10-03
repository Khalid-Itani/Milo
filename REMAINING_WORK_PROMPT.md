# Milo — finish my backend, verify it, push a branch, then merge

Complete my remaining Milo backend work end to end. Continue from the existing implementation;
do not restart, stop at a plan, or assume the current source is already working. Make routine
decisions yourself. Ask me only for genuinely missing information or external access.

This prompt becomes authorization to commit, push the backend branch, create a PR, and merge
it into main WHEN I return it to you after review and the verification gates below are met.
It does not authorize deployment, purchases, force-pushes, resets, deletion of user data,
or edits to my teammate's iOS/design files.

## Scope and starting point

- Repository: https://github.com/Khalid-Itani/Milo, previously Hackers-Healers; same repository.
- I own backend/, persistence, the Claude agent, Windows setup and backend documentation.
  My teammate owns ios/, SwiftUI/Xcode, Visualize SDK mapping and real iPhone testing.
- Retain FastAPI, Pydantic, SQLModel/SQLAlchemy, psycopg and the existing Anthropic SDK approach.
  Production persistence is Supabase Postgres; SQLite is only an explicit offline test adapter.
- Read applicable AGENTS.md/skills, root README/SPEC, backend/README, API_CONTRACT,
  IOS_HANDOFF, TEAM_STATUS and VERIFICATION, plus the actual implementation/tests. Read the
  current iOS models/client/call sites for compatibility, without editing them. Original Milo
  requirements still apply; this prompt changes the previous restriction against push/merge.
- The last recorded state had an unborn local main, read-only .git, all source untracked,
  only pip installed, eight stdlib tests passed and no full API/live checks. Recheck everything.
  The network diagnostic returned PermissionError / Windows 10013 against public PyPI.

## Finish the work

1. Repair the checkout safely. Preserve every existing change and secret. Recover the REAL
   GitHub history rather than making an unrelated initial commit. Use/validate GIT_RECOVERY
   and prepare_checkout.ps1 if necessary; stop for an explicit merge if upstream overlaps
   changed. Work on backend/supabase-agent (or a new backend-prefixed branch if already used).
   Re-read latest main and partner changes. Never reset, force-push or overwrite them.

2. Install all pinned requirements into the local venv using its python.exe directly. Verify
   Python/package compatibility and pip check. Fix genuine incompatible pins using official
   sources, rather than guessing or treating blocked networking as a missing release.
   If environment permissions/network still prevent an operation, don't bypass them or
   repeatedly retry. Give me the smallest required ordinary-PowerShell action, then continue
   all unaffected work. Don't ask for an execution-policy change or admin rights.

3. Run full pytest, the stdlib checks and scripts/verify_offline.py. Fix all failures and
   underlying backend issues. Actually exercise the five API stories: three-day dumbbell
   workout (legacy save and proposal/apply), vegetarian plan (not consumed food), keyed eggs
   and toast (one log), bench sets in repeat sessions (history preserved), and frequency
   goals based on dated completed sessions. Verify the existing iOS wire shapes, demo auth,
   fixed ownership, BMI, timezone/DST totals, target preservation, transactional saves,
   bounded/malformed/failed tools, durable retries/concurrency, proposal application, scan
   consent/deduplication, sanitized Visualize errors and rerunnable non-destructive seed.
   Offline tests must make no hosted/paid calls. Replace documentation OpenAPI with the
   actual runtime export and check fixtures against the real contract. Verify startup and
   shutdown. No silent fake-provider/database fallback or remaining core-flow placeholders.

4. Configure live services through ignored backend/.env only. If something is missing, ask
   me to fill it LOCALLY, not paste secrets in chat. Confirm the exact hackathon Supabase
   project reference before any hosted operation; never inspect/select unrelated projects.
   Use its Connect-dialog TLS URL and modest pooling, then apply reviewed Alembic migrations
   without drop/reset/import-time DDL. Keep RLS enabled on app tables in exposed schemas,
   deny anon/authenticated access, and check grants/available advisors. Run the safe explicit
   synthetic seed, verify write/read, then actually restart the backend and read the same
   records. Keep local SQLite files untouched. Resolve relevant advisor findings without
   broadening access. Verify current official Supabase/driver guidance before changes.

5. When configured, run separate, minimal live Claude and Visualize session checks. Verify
   supported model/tool behavior and the real stable-host-user session request, without
   printing tokens or keys. Do not claim a physical scan was tested from Windows. If live
   credentials/access remain unavailable, finish all offline implementation/testing and
   clearly record each live check as not run; do not manufacture successful results.

6. Verify/document Windows startup, PowerShell smoke requests and an HTTPS tunnel usable
   by the phone. No broad iOS transport exceptions. Update README, API_CONTRACT, real OpenAPI,
   fixtures, IOS_HANDOFF, TEAM_STATUS and VERIFICATION with actual outcomes and exact commands.
   Clearly separate what I finished from my remaining external setup and my teammate's work:
   demo header, stable retry keys, chat timeout, profile/targets/preferences, consent, repeat
   session IDs, Visualize token provider/actual SDK fields, refresh rules, optional proposal
   Save integration and device testing. Share only API URL/demo token/SDK publishable key
   privately; no server secrets belong in mobile code or Git.

## Publish and merge only after verification

7. Review the complete diff and staged files, check for secrets/unrelated edits, and confirm
   no ios/ or design/ changes. Full offline tests, runtime startup/export and diff checks must
   pass before publication; eight stdlib checks alone are not enough. Missing live credentials
   do not require fake success or prevent an otherwise verified backend merge, but their
   limitations must be prominent. Inspect workflows first: if push/merge would automatically
   deploy externally, stop and ask before triggering that deployment.

8. Commit the scoped implementation on the backend branch, push it normally, and open a PR
   into main with test evidence and remaining setup. Fetch latest main; safely integrate
   upstream changes, resolving only authorized backend/doc conflicts, and rerun affected
   tests. Wait for required CI/checks, preserve branch protections and required reviews, and
   merge the PR normally once green and allowed. Do not bypass checks or force changes into
   main. If a required review/conflict/access restriction blocks merging, report the exact
   next action rather than claiming success. Retain the backend branch unless I ask to delete it.

Finish with actual passed/failed/not-run checks, branch/commit/PR/merge references, confirmation
of the resulting remote main commit, exact run commands and a concise owner-by-owner handoff.
Distinguish implemented source, mocked tests, live checks, merging and deployment. Don't claim
everything is complete if an essential verification or authorized publish/merge step remains.

Database safety references: [Supabase connections](https://supabase.com/docs/guides/database/connecting-to-postgres)
and [RLS](https://supabase.com/docs/guides/database/postgres/row-level-security).
