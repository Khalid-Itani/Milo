"""Privacy and persistence boundaries that need more than successful HTTP responses."""
import json
from types import SimpleNamespace as NS
from uuid import uuid4

from fastapi.testclient import TestClient
from agent import coach
from app import db
from app.main import app
from tests.test_upgrade import EGGS, WORKOUT, mock_turn, scan_body


def test_read_tools_observe_writes_in_same_turn(c, monkeypatch):
    before = c.get("/today").json()["kcal"]["eaten"]
    seen = mock_turn(monkeypatch, [("get_today", {}), ("log_food", EGGS), ("get_today", {})])
    response = c.post("/chat", json={"message": "Log eggs and check my updated totals"})
    assert response.status_code == 200
    results = seen[-1]["messages"][-1]["content"]
    assert json.loads(results[0]["content"])["data"]["kcal"]["eaten"] == before
    assert json.loads(results[2]["content"])["data"]["kcal"]["eaten"] == before + 320


def test_today_tool_never_shares_storage_only_scan(c, monkeypatch):
    c.post("/profile", json={"scan_storage_consent": True})
    assert c.post("/scans", json=scan_body()).status_code == 200
    assert c.get("/today").json()["latest_scan"] is not None
    seen = mock_turn(monkeypatch, [("get_today", {})])
    assert c.post("/chat", json={"message": "Read my Today totals"}).status_code == 200
    data = json.loads(seen[-1]["messages"][-1]["content"][0]["content"])["data"]
    assert "latest_scan" not in data
    assert "waist_circumference" not in json.dumps(seen)


def test_conversation_context_does_not_mix_default_or_other_conversations(c, monkeypatch):
    seen = []
    def respond(**kwargs):
        seen.append(kwargs["messages"])
        return NS(stop_reason="end_turn", content=[NS(type="text", text="Hello.")])
    monkeypatch.setattr(coach, "create_message", respond)
    c.post("/chat", json={"message": "Named conversation only", "conversation_id": str(uuid4())})
    c.post("/chat", json={"message": "Default conversation only"})
    c.post("/chat", json={"message": "Another named conversation", "conversation_id": str(uuid4())})
    assert seen[1] == [{"role": "user", "content": "Default conversation only"}]
    assert seen[2] == [{"role": "user", "content": "Another named conversation"}]


def test_shutdown_disposes_cached_pool_without_creating_one(monkeypatch):
    db.get_engine.cache_clear()
    class FakePool:
        disposed = False
        def dispose(self):
            self.disposed = True
    pool = FakePool()
    monkeypatch.setattr(db.settings, "database_url", "postgresql+psycopg://demo@localhost/demo?sslmode=require")
    monkeypatch.setattr(db, "create_engine", lambda *a, **kw: pool)
    assert db.get_engine() is pool
    with TestClient(app) as client:
        assert client.get("/health").json() == {"ok": True}
    assert pool.disposed and db.get_engine.cache_info().currsize == 0
    monkeypatch.setattr(db.settings, "database_url", "")
    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
    assert db.get_engine.cache_info().currsize == 0


def test_legacy_card_data_has_swift_decoder_fields(c, monkeypatch):
    mock_turn(monkeypatch, [("create_workout_plan", WORKOUT), ("log_food", EGGS)])
    cards = c.post("/chat", json={"message": "Save my workout and food"}).json()["cards"]
    plan, food = cards
    assert {"plan_name", "weeks", "workouts"} <= plan["data"].keys()
    assert all({"id", "day_label", "name", "summary"} <= day.keys() for day in plan["data"]["workouts"])
    assert {"id", "meal", "name", "kcal", "protein_g", "carbs_g", "fat_g"} <= food["data"].keys()


def test_replacement_does_not_hide_active_session(c, monkeypatch):
    old = c.get("/workouts").json()[-1]
    assert c.post(f"/workouts/{old['id']}/start").status_code == 200
    replacement = WORKOUT | {"replaces_plan_id": old["plan_id"]}
    mock_turn(monkeypatch, [("create_workout_plan", replacement)])
    response = c.post("/chat", json={"message": "Replace my workout plan"}).json()
    assert response["cards"] == []
    assert len(c.get("/workouts?include_archived=true").json()) == 4
    mock_turn(monkeypatch, [("create_workout_plan", replacement)])
    card = c.post("/chat", json={"message": "Propose a replacement", "plan_mode": "propose"}).json()["cards"][0]
    assert c.post(f"/cards/{card['id']}/apply").status_code == 409
    assert c.get("/today").json()["next_workout"]["id"] == old["id"]
    assert c.post(f"/workouts/{old['id']}/finish").status_code == 200
    assert c.post(f"/cards/{card['id']}/apply").status_code == 200
    assert len(c.get("/workouts").json()) == 3
