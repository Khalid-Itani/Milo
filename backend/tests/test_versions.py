from types import SimpleNamespace as NS
from uuid import uuid4
from agent import coach
from app.config import settings
from tests.test_upgrade import WORKOUT, DIET, EGGS, mock_turn


def test_pending_diet_apply_and_history(c, monkeypatch):
    mock_turn(monkeypatch, [("create_diet_plan", DIET)])
    first = c.post("/chat", json={"message": "Create a diet", "plan_mode": "propose"}).json()["cards"][0]
    assert c.get("/diet-plans").json() == []
    before = c.get("/today").json()["kcal"]["eaten"]
    applied = c.post("/cards/"+first["id"]+"/apply", headers={"Idempotency-Key": "apply-diet"}).json()
    assert applied["status"] == "saved" and applied["data"]["status"] == "active"
    assert c.post("/cards/"+first["id"]+"/apply", headers={"Idempotency-Key": "apply-diet"}).json() == applied
    assert c.get("/today").json()["kcal"]["eaten"] == before
    old_id = c.get("/diet-plans").json()[0]["id"]
    mock_turn(monkeypatch, [("create_diet_plan", DIET | {"name": "Revised vegetarian day", "replaces_plan_id": old_id})])
    c.post("/chat", json={"message": "Revise my diet"})
    assert len(c.get("/diet-plans").json()) == 1
    all_versions = c.get("/diet-plans?include_archived=true").json()
    assert len(all_versions) == 2 and all_versions[-1]["status"] == "archived"


def test_request_id_and_conversation_context(c, monkeypatch):
    id, conversation = str(uuid4()), str(uuid4())
    seen = mock_turn(monkeypatch, [("log_food", EGGS)])
    body = {"message": "I ate eggs", "request_id": id, "conversation_id": conversation}
    a = c.post("/chat", json=body).json()
    assert c.post("/chat", json=body).json() == a
    history = c.get("/chat/history?conversation_id="+conversation).json()
    assert len(history) == 2
    assert len(seen) == 2 and seen[0]["messages"] == [{"role": "user", "content": "I ate eggs"}]
    assert c.get("/chat/history?conversation_id="+str(uuid4())).json() == []


def test_profile_constraints_in_context(c, monkeypatch):
    c.post("/profile", json={"preferences": ["vegetarian"], "allergies": ["peanuts"],
                            "equipment": ["dumbbells"], "experience": "beginner", "available_days": ["MON", "WED", "FRI"]})
    seen = mock_turn(monkeypatch, [("create_workout_plan", WORKOUT)])
    c.post("/chat", json={"message": "Build my plan"})
    system = seen[0]["system"]
    assert all(value in system for value in ("vegetarian", "peanuts", "dumbbells", "beginner", "FRI"))


def test_missing_visualize_credentials(c, monkeypatch):
    monkeypatch.setattr(settings, "visualize_secret_key", "")
    assert c.post("/visualize/session").status_code == 503


def test_successful_workout_replacement_preserves_sessions(c, monkeypatch):
    w = c.get("/workouts").json()[0]
    old_session = w["session_id"]
    mock_turn(monkeypatch, [("create_workout_plan", WORKOUT | {"replaces_plan_id": w["plan_id"]})])
    assert c.post("/chat", json={"message": "Replace my plan"}).status_code == 200
    assert len(c.get("/workouts").json()) == 3
    assert len(c.get("/workouts?include_archived=true").json()) == 7
    assert c.get(f"/sessions/{old_session}").json()["name"] == w["name"]
