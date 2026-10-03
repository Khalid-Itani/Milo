# FitCoach

A fitness app you drive by chatting with an AI coach. The Coach builds workout and diet plans, logs food and sets, and sets goals. The Today, Train, Eat and Goals tabs show what it saved. See `SPEC.md` for the full spec and `design/` for the mockups.

```
backend/   FastAPI + SQLite + Claude coach agent (backend/agent/)
ios/       SwiftUI app (iOS 17, XcodeGen)
```

## 1. Backend

```bash
cd backend
cp .env.example .env            # add ANTHROPIC_API_KEY (COACH_MODEL defaults to claude-opus-5-5)
python3 -m venv .venv && source .venv/bin/activate   # Python 3.11+
pip install -r requirements.txt
python -m app.seed              # mockup data; add --fresh to start with onboarding
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Tests: `pytest -q`. API docs: http://localhost:8000/docs

## 2. iOS

```bash
brew install xcodegen
cd ios && xcodegen && open FitCoach.xcodeproj
```

Run on an iPhone simulator. For a real device, set `Config.baseURL` to your Mac's LAN IP. To run without a backend, set `Config.useMock = true`. See `ios/README.md`.

## 3. Demo

With the backend running, `backend/scripts/demo_chat.sh` sends the demo prompts from `SPEC.md` section 6. For the full on-device demo:

1. Run `python -m app.seed --fresh`, launch the app and enter 180 cm / 74.6 kg. BMI 23.0 Normal appears on Today.
2. Coach: "I train 4 days a week and want a 100 kg bench by December. Build me a plan." The plan shows up in Train.
3. Coach: "Lunch was a chicken burrito bowl with guac". It appears under Lunch in Eat, and kcal left drops.
4. Coach: "What should I eat for dinner?"
5. Coach: "Set a goal: reach 72 kg by January 31". It appears in Goals.
6. Train: open Upper B, Start, tick 3 sets, Finish. Today shows 4 of 4 sessions.

## Known gaps

- The Visualize AI request in `backend/app/bmi.py` is a placeholder (`TODO(visualize)`). BMI falls back to the formula.
- Sleep and Resting HR tiles show "—" (no HealthKit). The mic, +, barcode and photo buttons do nothing.
- The dinner suggestion on Eat is hardcoded. Workout history ("previous" sets) shows the plan's targets.
