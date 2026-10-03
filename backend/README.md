# FitCoach backend

FastAPI + SQLite + a Claude coach with tool calling.

```bash
cd backend
cp .env.example .env            # add ANTHROPIC_API_KEY
python3 -m venv .venv && source .venv/bin/activate   # Python 3.11+
pip install -r requirements.txt
python -m app.seed              # mockup data (add --fresh to leave the profile empty and demo onboarding)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- Tests (LLM is mocked): `pytest -q`
- Demo prompts against the running server: `./scripts/demo_chat.sh`
- API docs: http://localhost:8000/docs

`COACH_MODEL` defaults to `claude-opus-5-5`. BMI uses the formula unless `VISUALIZE_API_KEY` and `VISUALIZE_API_URL` are set. The Visualize AI request in `app/bmi.py` is a best guess, so look for `TODO(visualize)` there.
