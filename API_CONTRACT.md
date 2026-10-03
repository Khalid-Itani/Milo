# Milo API contract

Version 2 extends the existing FitCoach phone wire format. Integer resource IDs, arrays,
snake_case fields, meal/kind/status enums and chat `{type, data}` cards are preserved.
Use HTTPS for the phone. Every business request requires `Authorization: Bearer <DEMO_API_TOKEN>`.
`GET /health` is public and returns exactly `{"ok":true}`; it does not probe the database.
The backend resolves DEMO_USER_ID; ownership fields such as id/owner_id/user_id are rejected in writes.

| Route | Input | Success |
|---|---|---|
| GET /profile | — | User |
| POST /profile | Existing height_cm, weight_kg, age, sex; fields now optional for partial updates | User |
| GET /today | Optional date=YYYY-MM-DD | Today |
| POST /chat | message; optional UUID request_id/conversation_id; plan_mode=save or propose | {reply,cards} |
| GET /chat/history | Optional conversation_id | ChatMessage array |
| GET /workouts | Optional include_archived=true | Workout array with exercises/sets |
| GET /workouts/{id} | integer ID | Workout |
| POST /workouts/{id}/start | no body | Workout |
| POST /workouts/{id}/finish | no body | Workout |
| POST /exercises/{id}/sets | kg,reps,is_warmup optional | WorkoutSet |
| PATCH /sets/{id} | kg/reps/done optional | WorkoutSet |
| GET /food | Optional date=YYYY-MM-DD | {date,meals:{breakfast,lunch,dinner,snack},totals} |
| POST /food | meal,name,kcal; optional quantity,macros,date,source,captured_at,provenance | FoodLog |
| DELETE /food/{id} | integer ID | {ok:true} |
| GET /diet-plans | Optional include_archived=true | DietPlan array |
| GET /goals | — | Goal array |
| POST /goals | title,kind,target_value and existing optional fields | Goal |
| PATCH /goals/{id} | current_value/status optional | Goal |

Existing card types and required data:

| type | data fields |
|---|---|
| workout_plan | plan_name,weeks,workouts[{id,day_label,name,summary}] |
| food_logged | id,meal,name,kcal,protein_g,carbs_g,fat_g |
| diet_plan | id,name,kcal,meals[{meal,name,kcal,protein_g,carbs_g,fat_g}] |
| goal_set | id,title,target_value,unit,deadline |
| set_logged | exercise,kg,reps |

Cards add optional id/status/action metadata; data is never renamed to payload.
Default chat saves plans immediately, matching the current navigation-only Save button.
Explicit logging and goals save immediately. Dinner suggestions do not become FoodLog records.
Only successful committed tools produce saved cards. Partial provider/tool failures return an
honest reply with any committed cards; already saved effects remain visible in the tabs.

## Additive APIs

| Route | Purpose |
|---|---|
| GET /sessions?workout_id= | Completed session array, newest first |
| GET /sessions/{id} | Legacy Workout shape for that historical session, with its actual sets |
| GET /cards | Pending card array for recovery after restart |
| POST /cards/{UUID}/apply | Apply pending plan atomically; returns the saved card; repeat safe |
| POST /visualize/session | Fresh SDK session_token/expires_at; never stored, replayed or cached |
| POST /scans | Consented summary ingestion with client_scan_id UUID |
| GET /scans | Up to 20 consented summaries, newest first; [] when storage consent is off |

Workout rows are immutable templates. Saving a plan prepares its first session/sets so
legacy detail screens get integer set IDs before Start. Starting uses those same prepared
IDs; starting after Finish creates fresh session/set IDs, preserving completed records.
Only one session may be active for the demo owner. Finish requires Start; repeating Finish
is safe. Set edits require an active session; stale completed-session set IDs return 409.
The legacy Workout status/start/finish/sets reflect its latest prepared, active or completed
session. Clients must refresh the workout after a repeat Start. Session statuses use
prepared/active/completed only in the new session-history API; legacy status remains
planned/active/done.

Replacements accept optional replaces_plan_id in Claude's plan tools. Previous versions are
archived, never deleted. New proposal-mode versions stay pending until application. Pending
workout IDs cannot be started directly. Application rechecks the replacement and conflicts
if it changed since the proposal. The session-history API still exposes archived-plan sessions.
Finish any active session before archiving its workout plan by replacement; proposal apply
returns 409 until then. Pending proposals can be created while a session is active.

## Replay protection

All legacy mutations accept optional `Idempotency-Key` (1–200 characters). Missing keys are
valid, including legacy requests with no body on Start/Finish. Generate a new UUID for each
intended action; reuse exactly that key and payload on network retries. Repeated successful
keyed requests return the persisted result, including after restart. Keys belong to the fixed
owner and cannot be reused on another route or payload: 409. Concurrent running chat requests
using the same key return 409 request_in_progress; retry after a short delay using the same key.

Optional chat request_id is a key when the header is absent; the header takes precedence.
conversation_id isolates the bounded model context but does not create another user identity.
Without either replay key, separate calls are separate turns and may duplicate intended logs.
The database enforces unique keys/effects, locks short owner transactions and fences chat
leases. A worker crash leaves a ten-minute lease; after expiry the same keyed request resumes
its persisted transcript. Provider calls hold no database transaction. Tool effects commit
with their journal entries; identical mutating tool name/input within one turn reuses that effect,
even when Claude sends a new tool ID. Multiple identical exercise sets need distinct
set_index values. Read tools execute freshly to observe intervening saves and current consent.
A completed partial-error response is also replayed; send a new action/key
to ask for a correction, acknowledging already saved records.

Exception: /visualize/session always mints a fresh token for each SDK preparation; never
reuse a request key to expect a cached token. Session tokens are not written to mutation records.

## Profile, targets, totals and dates

Optional profile fields: name, preferences/allergies/equipment string arrays, experience
(unspecified/beginner/intermediate/advanced), available_days (MON…SUN), goals_context,
timezone (IANA), kcal_target/protein_g/carbs_g/fat_g positive integer overrides,
scan_storage_consent and scan_ai_sharing_consent. Both consents default false.

BMI is round(weight_kg/(height_cm/100)^2,1); height/weight must be finite and positive.
Missing height/weight produces null BMI. Categories retain the existing values; BMI is not
body-fat percentage or a diagnosis. No Visualize BMI call exists.

Initial targets may be estimated only when all height/weight/age/sex inputs exist and no targets
have been set: Mifflin–St Jeor × 1.55, protein 2.2 g/kg, fat 25% of energy, remaining energy
as carbohydrate. These assumptions are not a clinical prescription. The response labels
targets_source=estimate_mifflin_st_jeor_activity_1.55. This preserves initial onboarding
behavior; later weight edits/logs never recalculate targets. Overrides are explicit.
Partial overrides require the remaining targets before Today can load.

The legacy Today decoder requires numeric targets. Until all four exist, GET /today returns
409 `{"detail":"profile_incomplete"}`; it never passes zeros off as personalized targets.
User targets remain nullable (the existing User decoder supports this).
Calorie left is signed. Eaten macros count only FoodLog records. Weekly completed-session
counts use dated sessions within Monday–Sunday in the user's timezone; days is seven booleans.
The weekly target comes from the newest active session goal or configured available days.
If neither exists, sessions_target=0 means no configured schedule, not a recommended target.
Strength/body goals use explicit updates, never invented 1RM or measurement progress.
Habit goals in unit=sessions use weekly_sessions; nutrition goals can opt into daily_protein.
Derived progress cannot be overridden through PATCH.

Timestamps require offsets on ingestion and store UTC. Date-only food requests mean noon
in the user's timezone on that date; no date means the local current day. An explicit date
and timestamp must agree. Aggregations use timezone-aware midnight boundaries (including
DST), not the server's day. Missing results are [] or optional null, and order is stable.

## Scan summaries

POST /scans requires client_scan_id, captured_at (ISO 8601 with offset), source
(visualize_sdk/manual/synthetic), metrics [{identifier,value,unit}] and optional source_metadata.
Identifiers use lowercase snake_case, are unique per scan, and are at most 64 characters.
Numeric values must be finite and positive; percent is at most 100. Explicit units are
cm/kg/percent. Source metadata accepts only sdk_version/device_model/mapping_version strings.
No frames, photos, arbitrary blobs or unselected raw ScanResult are accepted.

Example waist_circumference is illustrative until the partner confirms the actual SDK field.
There is no assumed body-fat or lean-mass result. visualizeme.ai SDK uploads are labeled
client-reported, not cryptographically verified or clinical DEXA. Manual/synthetic sources
are labeled accordingly. Storage consent is required before persistence. AI sharing additionally
requires the separate current AI consent; Today-only storage never grants model access.
The model's get_today tool always omits latest_scan, including when storage consent is on.
Permitted scan context is supplied separately after checking AI-sharing consent.
Revoking storage hides summaries from reads and Claude and blocks new ingestion; it does
not delete previously stored summaries. Reusing client_scan_id with identical input returns
the original record; different input returns 409.

## Errors and artifacts

401 unauthorized; 403 scan consent missing; 404 owned resource unavailable;
409 conflict/in-progress/incomplete profile; 422 sanitized validation; 502 provider error;
503 configuration/database unavailable; 504 Visualize timeout. Validation errors include
locations/types, never the supplied secrets or raw upstream/SQL messages.
Visualize defaults to https://api.visualizeme.ai; pilot override is explicit server configuration.
The session request is POST /v1/sessions with Bearer server secret and stable host_user_ref.

See [fixtures](backend/fixtures/README.md), [OpenAPI](backend/openapi.json), and
[iOS handoff](IOS_HANDOFF.md). The checked-in schema is the actual FastAPI runtime export.
Verification checks it against app.openapi() and validates examples against runtime models.
scripts/verify_offline.py exports it before running contract tests; CI rejects schema drift.
