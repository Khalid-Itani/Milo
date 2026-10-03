# Milo iOS handoff

No ios/ or design/ files were edited. FitCoach names/directories remain intact.
The backend preserves the existing integer IDs, arrays and card data fields.
The current phone app cannot connect unchanged: its APIClient sends no authorization.

## Required partner changes

1. Configure an HTTPS API base URL, disable Config.useMock for real backend traffic, and
   add the temporary demo header in APIClient.send before URLSession performs the request:

   ```swift
   req.setValue("Bearer \(Config.demoAPIToken)", forHTTPHeaderField: "Authorization")
   ```

   Put only the API base URL, demo token and Visualize publishable key in mobile configuration.
   No database, Claude or Visualize server secret belongs in Swift, Info.plist or responses.
   The temporary demo token is extractable from the app. This is controlled synthetic-data
   hackathon access, not multi-user production authorization. Rotate it when sharing ends.

2. Add optional Idempotency-Key support to the request helper. Generate one UUID per
   intentional write and retain that key, body and intended action across timeout/retry.
   Reuse it for POST/PATCH/DELETE retries; new intended writes get new keys. Existing calls
   without keys remain valid but lack replay protection. For chat, optional request_id also
   works as the key when the header is absent. A running-key 409 means retry the same action
   after a delay. Different payload on that key is a conflict, not a reason to resend it as
   a new write. Start/Finish retries should also retain keys.

3. Increase the chat timeout from the existing 60 seconds to about 300 seconds, or support
   a retained-key retry after a timeout. The bounded agent can take several provider calls.
   Do not recreate the action UUID after a lost response.

4. Handle Today 409 detail=profile_incomplete by prompting for the missing saved targets/
   profile. Successful Today still has numeric targets, matching the existing decoder.
   Existing onboarding height/weight/age/sex produces labeled initial estimates. Weight
   changes preserve prior targets. Preferences, allergies, equipment, experience, available
   days, goals context and explicit target overrides can be added to ProfileInput as optional
   fields. Display estimates appropriately. Targets are kcal and grams; heights cm/weights kg.
   Pass/consume the IANA timezone rather than assuming the Windows machine's day.

The existing Card enum still decodes type/data. It ignores new metadata, so keep default
plan_mode=save with the current navigation-only Save to Train button until proposal UI changes.
After repeat Start, refresh workouts and use the returned current session's new integer set
IDs; a stale completed-session set ID is intentionally read-only. Session-history APIs now
provide actual previous sets; the current Train PREVIOUS text still shows template targets.

## Optional proposal Save integration

Opt in by adding plan_mode="propose" to ChatInput. Extend the card wrapper/decoder to retain
id/status/action without changing data. For pending workout/diet cards, say proposed/pending,
and Save must POST /cards/{id}/apply with a stable action key, await success, then refresh
and navigate. Never navigate while implying a pending plan is already saved.
Apply returns the saved type/data card and is repeat-safe even without a key.
GET /cards recovers pending cards after restart. A pending plan never appears as active
Train/Eat data and cannot be activated by Start. Explicit logs/goals still save immediately.
Default save mode remains immediately saved, matching the existing Coach implementation.

## Visualize SDK boundary

You own SDK installation, Bundle ID/Team ID, TrueDepth capture, SDK callbacks and real-device
testing. In the SDK's token-provider callback, call authenticated POST /visualize/session for
each preparation or scan action and provide its session_token. Observe expires_at and mint
a fresh token when preparing again; do not cache the token or embed the server secret.
The backend sends the fixed host_user_ref=milo_demo_1 to POST /v1/sessions using its server key.
The backend does not receive camera frames, webhooks or server-delivered scan results.
The publishable SDK key comes separately from your Visualize configuration.

Scan storage and AI-sharing consent are separate profile toggles, default false. Request
storage consent before uploading any summary; AI sharing requires its own explicit consent.
With AI consent off, saved scans may appear on Today but are excluded from Claude's context.
Revocation hides summaries and blocks new uploads; it does not delete existing records.

Map only selected fields from the actual SDK ScanResult to POST /scans. Confirm exact SDK
names, units, and whether each metric exists before shipping the mapping. No result mapping
or physical scan was verified here. Example waist_circumference is illustrative, not a claim
that the SDK returns that field. Do not invent body-fat/lean-mass data or derive it from BMI.

Representative payload (manual example; use visualize_sdk only for actual SDK output):

```json
{
  "client_scan_id": "39a4c95c-e841-45e7-9e12-f199063c1945",
  "captured_at": "2026-10-03T12:00:00Z",
  "metrics": [{"identifier":"waist_circumference","value":82,"unit":"cm"}],
  "source": "manual",
  "source_metadata": {"mapping_version":"illustrative-v1"}
}
```

Generate client_scan_id once for each captured result and retain it through ingestion retries.
Use a stable Idempotency-Key too. Values must be finite/positive with explicit cm/kg/percent
units; percentages cannot exceed 100. Identifiers are lowercase snake_case, unique in the
summary. captured_at must include an offset. Send source_metadata only from
sdk_version/device_model/mapping_version. Do not upload the entire ScanResult, frames or images.
Actual SDK uploads are marked client-reported, not cryptographically verified or clinical DEXA.
GET /scans returns an array; Today adds optional latest_scan. Add Swift models only when ready.

## Refresh after writes

| Write | Refresh |
|---|---|
| Profile/targets/preferences/consent | profile, Today, goals; scans when consent changes |
| Chat | history, Today, workouts, food, diet-plans, goals, pending cards |
| Apply workout card | workouts, Today, pending cards, history if displaying card state |
| Apply diet card | diet-plans, pending cards |
| Start/set edits/Finish | workouts/session detail; Today and goals after Finish |
| Food log/delete | food, Today, goals |
| Goal create/update | goals, Today (weekly target may change) |
| Scan ingestion | scans, Today |

Chat history retains the original card snapshot; GET /cards/apply responses hold the current
proposal state. Do not treat an old pending snapshot as proof application failed.
The current AppStore already refreshes Today, food, workouts and goals after chat. Add diet
plans/cards/scan refreshes only for those integrations. The hardcoded salmon dinner box in
EatView remains partner-owned; replace it with a genuine suggestion when using preferences/
allergies. Its explicit Log it action is consumed food; merely asking for dinner is not.

## Phone transport and shared acceptance

A real iPhone cannot reach Windows localhost. Follow the documented Cloudflare Quick Tunnel
in backend/README.md, use its HTTPS URL in Config.baseURL, and confirm /health from the phone.
The tunnel process and backend must stay running; a Quick Tunnel URL can change on restart.
No broad App Transport Security exception is required for HTTPS.
Tunnel instructions were checked against Cloudflare documentation; a live tunnel remains
pending backend DATABASE_URL configuration. Actual iPhone scan testing belongs on your Mac/device.

Use backend/fixtures as decoder examples and API_CONTRACT.md for errors/retry behavior.
Fixtures validate against runtime FastAPI/Pydantic output. The full offline suite passed
50 tests plus actual Windows PowerShell and process-restart checks on a disposable database.
The confirmed Supabase schema and live backend seed/write/read/process-restart checks passed.
Claude/Visualize live checks still need keys. No Swift files changed; no physical scan tested.
Run the five stories with the backend owner: dumbbell plan (save/propose), vegetarian plan
(no eaten calories), eggs/toast (one keyed log), bench sets (correct current session and
preserved history), frequency goal (real completed-session progress). Live provider calls
are separate from offline mocks; never present mocked results as physical scan verification.
