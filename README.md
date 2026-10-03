# FitCoach — hackathon starter

1. Unzip into an empty folder named `fitcoach` and `git init`.
2. Open Claude Code in that folder.
3. Paste one of the prompts below.

## One-shot (one person, whole app)

```
Read SPEC.md and every file in design/ first. Then build the entire app exactly as specified: backend, agent and iOS, following the build order in section 5. Use the exact API shapes in section 2.2. Run the backend tests and the demo_chat.sh script before moving to iOS, and fix anything that fails. Leave the Visualize AI call as a clearly marked TODO with the BMI formula fallback working. Finish with a root README that explains how to run both halves.
```

## Split (two people, two Claude Code sessions)

Person B — backend + agent:
```
Read SPEC.md. Build only backend/ (sections 2 and 3, build-order steps 1–2). Use the exact API shapes in section 2.2. Seed the data in 2.4, run the tests, and write backend/scripts/demo_chat.sh covering the demo prompts in section 6.
```

Person A — iOS:
```
Read SPEC.md and every file in design/. Build only ios/ (section 4, build-order steps 3–4). Match the mockups in design/ closely. Decode the exact JSON shapes in section 2.2. Until the backend is up, use a MockAPIClient that returns the seed values from section 2.4, behind a flag in Config.swift.
```

## Before you start
- Put `ANTHROPIC_API_KEY`, `COACH_MODEL`, and (if you have them) `VISUALIZE_API_KEY` / `VISUALIZE_API_URL` in `backend/.env`.
- `brew install xcodegen` on the iOS machine.
