"""Adapted legacy API tests: same wire shapes, explicit access header and test adapter."""
from types import SimpleNamespace as NS
from agent import coach
from app.bmi import bmi_formula, category

def test_today_totals(c):
    t = c.get("/today").json()
    assert t["kcal"] == {"target": 2450, "eaten": 1620, "left": 830}
    assert t["macros"]["protein"] == {"eaten": 124, "target": 160}
    assert t["macros"]["carbs"]["eaten"] == 172 and t["macros"]["fat"]["eaten"] == 48
    assert t["bmi"] == {"value": 23.0, "category": "Normal"}
    assert t["next_workout"]["name"] == "Upper B — Volume"
    assert t["next_workout"]["exercise_count"] == 4

def test_bmi_and_preserved_targets(c):
    assert bmi_formula(180, 74.6) == 23.0 and category(23.0) == "Normal"
    u = c.post("/profile", json={"height_cm": 180, "weight_kg": 74.6, "age": 21, "sex": "male"}).json()
    assert (u["bmi"], u["bmi_category"]) == (23.0, "Normal")
    assert u["kcal_target"] == 2450
    assert c.post("/profile", json={"weight_kg": 80}).json()["protein_g"] == 160

def test_food_updates_today(c):
    f = c.post("/food", json={"meal": "dinner", "name": "Salmon bowl", "quantity": "1", "kcal": 780,
                              "protein_g": 45, "carbs_g": 80, "fat_g": 25}).json()
    assert c.get("/today").json()["kcal"]["left"] == 50
    assert c.get("/food").json()["meals"]["dinner"][0]["id"] == f["id"]
    assert c.delete(f"/food/{f['id']}").json() == {"ok": True}
    assert c.get("/today").json()["kcal"]["left"] == 830

def test_finish_workout_updates_week(c):
    before = c.get("/today").json()["week"]["sessions_done"]
    w = c.get("/workouts").json()[-1]
    assert c.post(f"/workouts/{w['id']}/start").json()["status"] == "active"
    set_id = w["exercises"][0]["sets"][0]["id"]
    assert c.patch(f"/sets/{set_id}", json={"done": True, "reps": 9}).json()["reps"] == 9
    assert c.post(f"/workouts/{w['id']}/finish").json()["status"] == "done"
    assert c.get("/today").json()["week"]["sessions_done"] == before+1

def test_goals_crud(c):
    g = c.post("/goals", json={"title": "Squat 140", "kind": "strength", "unit": "kg", "start_value": 120,
                               "current_value": 120, "target_value": 140, "deadline": "2027-03-01"}).json()
    assert c.patch(f"/goals/{g['id']}", json={"current_value": 130}).json()["current_value"] == 130

def test_chat_tool_loop(c, monkeypatch):
    replies = iter([
        NS(stop_reason="tool_use", content=[NS(type="tool_use", id="t1", name="log_food", input={
            "meal": "dinner", "name": "Steak and rice", "quantity": "1 plate",
            "kcal": 700, "protein_g": 50, "carbs_g": 70, "fat_g": 20})]),
        NS(stop_reason="end_turn", content=[NS(type="text", text="Logged. 130 kcal left.")]),
    ])
    monkeypatch.setattr(coach, "create_message", lambda **kw: next(replies))
    r = c.post("/chat", json={"message": "Dinner was steak and rice"}).json()
    assert r["reply"] == "Logged. 130 kcal left."
    assert r["cards"][0]["type"] == "food_logged" and r["cards"][0]["data"]["kcal"] == 700
    assert c.get("/today").json()["kcal"]["left"] == 130
    assert c.get("/chat/history").json()[-1]["cards"][0]["type"] == "food_logged"
