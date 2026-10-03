# FitCoach — Build Spec (Hackathon MVP)

Chat-first fitness app. A Coach chat creates workouts and diet plans, logs food and workouts, and sets goals. Four other tabs show what the Coach saved. Think: lifting tracker + food diary, driven by an AI coach.

Three parts in one monorepo:
1. `backend/` — REST API + SQLite
2. `backend/agent/` — LLM coach with tool calling (lives inside the backend)
3. `ios/` — SwiftUI app, 5 tabs

Reference designs are in `design/*.html` (static HTML mockups at 390×844). Match their layout, copy, colors and type as closely as SwiftUI allows. Read them before building any iOS screen.

---

## 0. Ground rules for the build

- Single hardcoded user (`user_id = 1`). No auth.
- Prefer working end-to-end over completeness. Every tab must render real data from the API.
- No HealthKit, no barcode scanning, no photo logging, no push notifications. Buttons for those may exist in the UI but do nothing.
- All weights in kg, energy in kcal, macros in grams.
- Keep secrets in `backend/.env` (never commit). Provide `backend/.env.example`.

---

## 1. Repo layout

```
fitcoach/
  SPEC.md
  design/                 # reference mockups (do not modify)
  backend/
    app/
      main.py             # FastAPI app + routes
      db.py               # SQLite + SQLModel setup
      models.py           # tables
      schemas.py          # response shapes
      seed.py             # sample data
      bmi.py              # Visualize AI client + fallback
      today.py            # /today aggregation
    agent/
      coach.py            # chat loop with tool calling
      tools.py            # tool schemas + implementations
      prompt.py           # system prompt
    tests/
      test_api.py
    requirements.txt
    .env.example
    README.md
  ios/
    project.yml           # XcodeGen spec
    FitCoach/
      App.swift
      Config.swift        # API base URL
      Theme.swift         # colors, fonts
      API/                # APIClient.swift, Models.swift
      Views/
        TodayView.swift
        CoachView.swift
        TrainView.swift
        WorkoutDetailView.swift
        EatView.swift
        GoalsView.swift
        OnboardingView.swift
        Components/       # Ring, MacroBar, Cards, TabBar styling
    README.md
```

---

## 2. Backend

**Stack:** Python 3.11+, FastAPI, SQLModel (SQLite file `fitcoach.db`), Uvicorn, `anthropic` SDK, `httpx`.

Run: `cd backend && pip install -r requirements.txt && python -m app.seed && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`

### 2.1 Data models

| Table | Fields |
|---|---|
| User | id, name, height_cm, weight_kg, age, sex (`male`/`female`), kcal_target, protein_g, carbs_g, fat_g, bmi (float, nullable), bmi_category (str, nullable) |
| Workout | id, name, day_label (e.g. `MON`), notes, status (`planned`/`active`/`done`), started_at, finished_at, plan_id (nullable) |
| Exercise | id, workout_id, name, position, target_sets, target_reps, target_kg (nullable) |
| WorkoutSet | id, exercise_id, set_index, kg, reps, is_warmup, done |
| FoodLog | id, date (YYYY-MM-DD), meal (`breakfast`/`lunch`/`dinner`/`snack`), name, quantity (str), kcal, protein_g, carbs_g, fat_g, source (`manual`/`coach`) |
| DietPlan | id, name, kcal, meals (JSON: list of `{meal, name, kcal, protein_g, carbs_g, fat_g}`), created_at |
| Goal | id, title, kind (`strength`/`body`/`nutrition`/`habit`), unit, start_value, current_value, target_value, deadline (date, nullable), status (`active`/`completed`) |
| ChatMessage | id, role (`user`/`assistant`), content, cards (JSON), created_at |

### 2.2 Endpoints

All responses are JSON. Use these exact shapes; iOS decodes them.

```
GET  /health                      -> {"ok": true}

POST /profile                     body {height_cm, weight_kg, age, sex}
                                  -> User (recomputes BMI via bmi.py, sets kcal/macro targets with Mifflin-St Jeor × 1.55)
GET  /profile                     -> User

GET  /today                       -> Today
POST /chat                        body {message} -> {reply: str, cards: Card[]}
GET  /chat/history                -> ChatMessage[]

GET  /workouts                    -> Workout[] (with exercises + sets)
GET  /workouts/{id}               -> Workout
POST /workouts/{id}/start         -> Workout (status=active, started_at=now)
POST /workouts/{id}/finish        -> Workout (status=done)
POST /exercises/{id}/sets         body {kg, reps, is_warmup?} -> WorkoutSet
PATCH /sets/{id}                  body {kg?, reps?, done?} -> WorkoutSet

GET  /food?date=YYYY-MM-DD        -> {date, meals: {breakfast: FoodLog[], lunch: [...], dinner: [...], snack: [...]}, totals: Macros}
POST /food                        body FoodLog fields (no id) -> FoodLog
DELETE /food/{id}                 -> {"ok": true}

GET  /diet-plans                  -> DietPlan[]
GET  /goals                       -> Goal[]
POST /goals                       body Goal fields (no id) -> Goal
PATCH /goals/{id}                 body {current_value?, status?} -> Goal
```

`Today` shape:
```json
{
  "date": "2026-10-03",
  "kcal": {"target": 2450, "eaten": 1620, "left": 830},
  "macros": {
    "protein": {"eaten": 124, "target": 160},
    "carbs":   {"eaten": 172, "target": 260},
    "fat":     {"eaten": 48,  "target": 75}
  },
  "bmi": {"value": 23.0, "category": "Normal"},
  "weight_kg": 74.6,
  "week": {"sessions_done": 3, "sessions_target": 4, "days": [true, true, false, true, false, false, false]},
  "next_workout": {"id": 4, "name": "Upper B — Volume", "exercise_count": 4, "est_minutes": 55},
  "coach_tip": "36 g protein to go. A salmon rice bowl for dinner closes it at 780 kcal."
}
```
`coach_tip`: one short sentence generated from today's numbers (rule-based is fine; no LLM call needed).

`Card` (returned by `/chat`, stored on ChatMessage):
```json
{"type": "workout_plan", "data": {"plan_name": "Upper / Lower · 4 days", "weeks": 8, "workouts": [{"id": 1, "day_label": "MON", "name": "Upper A — Strength", "summary": "Bench 5×5 · Row · Overhead press · Pull-up"}]}}
{"type": "food_logged",  "data": {"id": 12, "meal": "lunch", "name": "Chicken burrito bowl, guacamole", "kcal": 680, "protein_g": 42, "carbs_g": 71, "fat_g": 24}}
{"type": "diet_plan",    "data": {"id": 2, "name": "...", "kcal": 2400, "meals": [...]}}
{"type": "goal_set",     "data": {"id": 3, "title": "Reach 72 kg", "target_value": 72, "unit": "kg", "deadline": "2027-01-31"}}
{"type": "set_logged",   "data": {"exercise": "Bench Press", "kg": 75, "reps": 8}}
```

### 2.3 BMI via Visualize AI (`app/bmi.py`)

- `async def compute_bmi(height_cm, weight_kg) -> (value: float, category: str, source: str)`
- If `VISUALIZE_API_KEY` and `VISUALIZE_API_URL` are set, call Visualize AI. **TODO for the team: fill in the exact endpoint, auth header and request/response mapping from Visualize AI's docs.** Leave a clearly marked `# TODO(visualize)` block with a best-guess `httpx.post` and a timeout of 5 s.
- On any error, missing key or timeout, fall back to `weight_kg / (height_cm/100)**2`, rounded to 1 decimal. Categories: <18.5 Underweight, <25 Normal, <30 Overweight, else Obese.
- Log which source was used.

### 2.4 Seed data (`app/seed.py`)

Idempotent (drop and recreate). The values match the mockups:
- User: Agam, 180 cm, 74.6 kg, 21, male; targets 2450 kcal / 160 P / 260 C / 75 F.
- Plan "Upper / Lower · 4 days" with workouts: MON Upper A — Strength (done), TUE Lower A (done), THU Lower B (done), SAT Upper B — Volume (planned: Bench Press 4×8 @75, Incline DB Press 3×10 @30, Cable Fly 3×12 @17.5, Lateral Raise 3×15 @10).
- Today's food: breakfast (Greek yogurt 2% 250 g 183 kcal; Granola 45 g 205; Blueberries 1 cup 84; Latte 12 oz 58), lunch (Chicken burrito bowl, guacamole 680, 42/71/24, source coach), snack (Protein shake 210; Banana 105; Peanut butter 1 tbsp 95). Fill plausible macros so totals ≈ 124 P / 172 C / 48 F.
- Goals: Bench press 100 kg (strength, start 85, current 95, deadline Dec 15); Reach 72 kg (body, start 76.8, current 74.6, deadline Jan 31); 160 g protein daily (nutrition, habit-style, current 124); Train 4× a week (habit, current 3, target 4).

### 2.5 Tests (`tests/test_api.py`)
pytest + FastAPI TestClient: seed, then assert `/today` totals, BMI fallback math (180 cm / 74.6 kg → 23.0), creating food updates `/today`, finishing a workout updates `week.sessions_done`. Mock the LLM; don't call the real API in tests.

---

## 3. Agent (`backend/agent/`)

**Model:** Anthropic Messages API with tool use. Model name from env `COACH_MODEL`, API key from `ANTHROPIC_API_KEY`. Loop: send messages + tools → execute any `tool_use` blocks against the DB → send `tool_result` → repeat until `stop_reason == "end_turn"` (max 6 iterations).

**Context per turn:** last 20 ChatMessages + a system-prompt block with the current `/today` JSON, profile, active goals and the next workout.

**System prompt (`prompt.py`), essentials:**
- You are Coach, a concise strength + nutrition coach inside a fitness app.
- Replies are 1–3 short sentences. No emoji. No markdown headers.
- Always save things with tools; never just describe a plan without saving it.
- When the user describes food, estimate portions and macros sensibly, call `log_food`, then state kcal and protein left today.
- When asked for a training plan, call `create_workout_plan` with 3–5 workouts, each 4–6 exercises with sets/reps/kg.
- Use the provided "today" context; don't invent numbers that contradict it.

**Tools (`tools.py`)** — each returns JSON and produces one Card:

| Tool | Input | Effect | Card |
|---|---|---|---|
| `create_workout_plan` | plan_name, weeks, workouts[{day_label, name, exercises[{name, sets, reps, kg?}]}] | inserts Workouts + Exercises (+ empty sets) | workout_plan |
| `log_workout_set` | exercise_name, kg, reps | finds exercise in active (or next) workout, adds a done set | set_logged |
| `log_food` | meal, name, quantity, kcal, protein_g, carbs_g, fat_g | inserts FoodLog (source=coach, date=today) | food_logged |
| `create_diet_plan` | name, kcal, meals[{meal, name, kcal, protein_g, carbs_g, fat_g}] | inserts DietPlan | diet_plan |
| `set_goal` | title, kind, unit, start_value, target_value, deadline? | inserts Goal | goal_set |
| `get_today` | — | returns Today JSON | none |

`/chat` persists the user message, runs the loop, persists the assistant message with collected cards, and returns `{reply, cards}`.

---

## 4. iOS app

**Stack:** SwiftUI, iOS 17+, async/await, no third-party packages. Project generated with XcodeGen (`brew install xcodegen && cd ios && xcodegen`), bundle id `com.hackathon.fitcoach`.

`Config.swift`: `static let baseURL = URL(string: "http://localhost:8000")!` with a comment that a real device needs the Mac's LAN IP or an ngrok URL. Add `NSAppTransportSecurity > NSAllowsArbitraryLoads = true` in Info for the hackathon.

### 4.1 Theme (from the mockups)

| Token | Value | Use |
|---|---|---|
| background | #F5F5F2 | screen ground |
| surface | #FFFFFF | cards (corner radius 18–22) |
| ink | #111214 | text, primary buttons, user chat bubbles |
| secondary text | #5E636C | captions |
| hairline | #F0EFEC / #E4E3DF | dividers, tab bar border |
| train accent | #F25C1F | anything training: steps bar, week bars, Start/Finish buttons, done-set checks (dark text on it) |
| done-set row tint | #FFF1EA | |
| fuel accent | #2E64E8 | anything nutrition: calorie ring, protein bar, "Log it" |
| carbs | #8FB0F5 | |
| fat | #A3A8B0 | |
| fuel tint | #F1F4FB / #E8EDF8 | Coach suggestion boxes |

Fonts: SF Pro (system) for text; `.monospacedDigit()` or SF Mono for all numbers. Large titles 28–32 pt bold, tight tracking. Touch targets ≥ 44 pt. No emoji anywhere.

### 4.2 Tabs (TabView, in this order)
`Today` (square.grid.2x2), `Coach` (bubble.left), `Train` (dumbbell), `Eat` (fork.knife), `Goals` (target). Active tint = ink.

### 4.3 Screens — see `design/<Name>.html` for exact layout

- **Today** (`design/Today.html`): date + "Today" title; dark Coach tip card (tap → Coach tab); calorie ring (kcal left in center) + 3 macro bars; 2×2 metric grid — **BMI** (value + category, replaces Steps from mockup), Weight, plus two tiles with placeholder "—" for Sleep and Resting HR (no HealthKit); "This week" 7-day bars + next workout row with orange Start button (→ Train, starts the workout). Pull to refresh.
- **Coach** (`design/Coach.html`): message list (user = dark bubble right; coach = plain text left); render each Card type as a native card — workout_plan shows day rows + "Save to Train" (just switches to Train tab, plan is already saved) and "Adjust" (prefills input "Adjust the plan: "); food_logged shows check icon, "Logged to <Meal>", name, kcal, P/C/F chips, Undo (DELETE /food/{id}); suggestion chips above the input ("Plan tonight's dinner", "Swap an exercise", "How was my week?") that send immediately; input bar with + (no-op), text field, mic (no-op), send. Show a typing indicator while waiting. Load `/chat/history` on appear.
- **Train** (`design/Train.html`): list of workouts grouped by status (Active / Up next / Done). Tapping opens **WorkoutDetailView**: title, Finish button, stats strip (duration since started_at, volume = Σ kg×reps of done sets, sets done), per-exercise card with a SET / PREVIOUS / KG / REPS / ✓ grid; editable kg and reps fields; tapping ✓ PATCHes `done=true` and tints the row; "Add set" button. Skip the rest timer UI or show it static.
- **Eat** (`design/Eat.html`): day header ("Today"); Goal − Food = Left equation + 3 macro bars; "Describe what you ate…" field that sends `"Log for <meal by time of day>: <text>"` to `/chat` and refreshes; meal sections (Breakfast, Lunch, Snacks, Dinner) with item rows (name, quantity, macros, "via Coach" tag when source=coach, kcal); swipe to delete. If Dinner is empty, show the blue "Coach suggests" box — fetch via `/chat` with "Suggest one dinner that fits my remaining macros" lazily, or hardcode from `coach_tip` for speed; "Log it" logs it, "Other ideas" → Coach tab.
- **Goals** (`design/Goals.html`): "New goal" button (→ Coach tab with input prefilled "Set a goal: "); Active / Completed segmented control; large cards for strength and body goals (current / target, progress bar = (current−start)/(target−start), deadline); compact 2-column cards for nutrition and habit goals; dashed "Tell Coach what you want to achieve" row → Coach.
- **Onboarding** (sheet on first launch, when `/profile` has no height): height cm, weight kg, age, sex picker → POST /profile → show resulting BMI → dismiss.

### 4.4 Networking
`APIClient` actor with generic `get/post/patch/delete`, JSON snake_case ↔ camelCase via `keyDecodingStrategy = .convertFromSnakeCase`. One `@Observable AppStore` holding today, workouts, food, goals, chat; each tab calls `refresh()` on appear. Cross-tab navigation via a `selectedTab` binding in AppStore.

---

## 5. Build order (for a single Claude Code run)

1. Backend models, db, seed, all non-chat endpoints, `/today`, BMI with fallback. Run tests.
2. Agent: tools, prompt, `/chat` loop. Verify with a curl script (`backend/scripts/demo_chat.sh`) for the 5 demo prompts below.
3. iOS: XcodeGen project, Theme, APIClient + models, AppStore.
4. iOS screens in order: Today → Coach → Eat → Train → Goals → Onboarding.
5. Root README with run steps for both halves and the demo script.

If two people split it: Person A runs step 3–4 (iOS) against the seeded backend; Person B runs steps 1–2. The contract in §2.2 is the shared boundary.

## 6. Acceptance criteria / demo script

1. Fresh launch → onboarding → enter 180 cm / 74.6 kg → BMI 23.0 Normal appears on Today.
2. Coach: "I train 4 days a week and want a 100 kg bench by December. Build me a plan." → workout_plan card → Train tab lists 4 workouts.
3. Coach: "Lunch was a chicken burrito bowl with guac" → food_logged card → Eat shows it under Lunch with "via Coach"; Today's kcal-left drops.
4. Coach: "What should I eat for dinner?" → a suggestion that fits the remaining kcal (diet_plan card or text).
5. Coach: "Set a goal: reach 72 kg by January 31" → goal_set card → appears in Goals.
6. Train: open Upper B, Start, tick 3 sets → volume and set count update; Finish → Today week bars show 4 of 4.
