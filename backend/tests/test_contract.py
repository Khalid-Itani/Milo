"""Validate examples against FastAPI's runtime schema and Pydantic response models."""
import json
from pathlib import Path
from pydantic import TypeAdapter
from app import schemas as sh
from app.main import app
from app.visualize import SessionToken
from offline_tests.test_stdlib import validate

ROOT = Path(__file__).resolve().parents[1]


def test_checked_in_openapi_is_runtime_export():
    assert json.loads((ROOT / "openapi.json").read_text(encoding="utf-8")) == app.openapi()


def test_fixtures_match_runtime_models_and_schema():
    mapping = {"profile": sh.UserOut, "today": sh.TodayOut, "chat": sh.ChatOut,
               "proposal": sh.ChatOut, "food": sh.FoodDayOut, "visualize-session": SessionToken,
               "workouts": list[sh.WorkoutOut], "diet-plans": list[sh.DietOut],
               "goals": list[sh.GoalOut], "scans": list[sh.ScanOut],
               "chat-history": list[sh.ChatMessageOut]}
    schema = app.openapi()
    for name, model in mapping.items():
        data = json.loads((ROOT / "fixtures" / (name + ".json")).read_text(encoding="utf-8"))
        TypeAdapter(model).validate_python(data)
        if isinstance(data, list):
            for item in data:
                validate(item, schema["components"]["schemas"][model.__args__[0].__name__])
        else:
            validate(data, schema["components"]["schemas"][model.__name__])
