import logging
from datetime import date as Date, datetime

from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import Session, select

from agent import coach
from app.bmi import compute_bmi
from app.db import get_session, init_db
from app.models import ChatMessage, DietPlan, Exercise, FoodLog, Goal, User, Workout, WorkoutSet
from app.schemas import ChatIn, GoalPatch, ProfileIn, SetIn, SetPatch, workout_out
from app.today import build_today, food_totals

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="FitCoach")
init_db()

MEALS = ("breakfast", "lunch", "dinner", "snack")


def today_str() -> str:
    return Date.today().isoformat()


def get_or_404(s: Session, model, id: int):
    obj = s.get(model, id)
    if not obj:
        raise HTTPException(404, f"{model.__name__} {id} not found")
    return obj


def save(s: Session, obj):
    s.add(obj)
    s.commit()
    s.refresh(obj)
    return obj


def user(s: Session) -> User:
    return s.get(User, 1) or save(s, User(id=1))


@app.get("/health")
def health():
    return {"ok": True}


@app.get("/profile")
def get_profile(s: Session = Depends(get_session)):
    return user(s)


@app.post("/profile")
async def post_profile(body: ProfileIn, s: Session = Depends(get_session)):
    u = user(s)
    for k, v in body.model_dump().items():
        setattr(u, k, v)
    u.bmi, u.bmi_category, _ = await compute_bmi(body.height_cm, body.weight_kg)
    # Mifflin-St Jeor × 1.55 (moderately active)
    bmr = 10 * body.weight_kg + 6.25 * body.height_cm - 5 * body.age + (5 if body.sex == "male" else -161)
    u.kcal_target = round(bmr * 1.55)
    u.protein_g = round(2.2 * body.weight_kg)
    u.fat_g = round(u.kcal_target * 0.25 / 9)
    u.carbs_g = round((u.kcal_target - u.protein_g * 4 - u.fat_g * 9) / 4)
    return save(s, u)


@app.get("/today")
def today(s: Session = Depends(get_session)):
    user(s)
    return build_today(s)


@app.post("/chat")
def chat(body: ChatIn, s: Session = Depends(get_session)):
    user(s)
    return coach.run(s, body.message)


@app.get("/chat/history")
def chat_history(s: Session = Depends(get_session)):
    return s.exec(select(ChatMessage).order_by(ChatMessage.id)).all()


@app.get("/workouts")
def workouts(s: Session = Depends(get_session)):
    return [workout_out(s, w) for w in s.exec(select(Workout).order_by(Workout.id)).all()]


@app.get("/workouts/{id}")
def workout(id: int, s: Session = Depends(get_session)):
    return workout_out(s, get_or_404(s, Workout, id))


@app.post("/workouts/{id}/start")
def start_workout(id: int, s: Session = Depends(get_session)):
    w = get_or_404(s, Workout, id)
    w.status, w.started_at = "active", datetime.now()
    return workout_out(s, save(s, w))


@app.post("/workouts/{id}/finish")
def finish_workout(id: int, s: Session = Depends(get_session)):
    w = get_or_404(s, Workout, id)
    w.status, w.finished_at = "done", datetime.now()
    w.started_at = w.started_at or w.finished_at
    return workout_out(s, save(s, w))


@app.post("/exercises/{id}/sets")
def add_set(id: int, body: SetIn, s: Session = Depends(get_session)):
    get_or_404(s, Exercise, id)
    n = len(s.exec(select(WorkoutSet).where(WorkoutSet.exercise_id == id)).all())
    return save(s, WorkoutSet(exercise_id=id, set_index=n, **body.model_dump()))


@app.patch("/sets/{id}")
def patch_set(id: int, body: SetPatch, s: Session = Depends(get_session)):
    ws = get_or_404(s, WorkoutSet, id)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(ws, k, v)
    return save(s, ws)


@app.get("/food")
def food(date: str | None = None, s: Session = Depends(get_session)):
    date = date or today_str()
    items = s.exec(select(FoodLog).where(FoodLog.date == date).order_by(FoodLog.id)).all()
    return {
        "date": date,
        "meals": {m: [f for f in items if f.meal == m] for m in MEALS},
        "totals": food_totals(s, date),
    }


@app.post("/food")
def add_food(body: FoodLog, s: Session = Depends(get_session)):
    body.id = None
    return save(s, FoodLog.model_validate(body.model_dump(warnings=False)))


@app.delete("/food/{id}")
def delete_food(id: int, s: Session = Depends(get_session)):
    s.delete(get_or_404(s, FoodLog, id))
    s.commit()
    return {"ok": True}


@app.get("/diet-plans")
def diet_plans(s: Session = Depends(get_session)):
    return s.exec(select(DietPlan).order_by(DietPlan.id.desc())).all()


@app.get("/goals")
def goals(s: Session = Depends(get_session)):
    return s.exec(select(Goal).order_by(Goal.id)).all()


@app.post("/goals")
def add_goal(body: Goal, s: Session = Depends(get_session)):
    body.id = None
    return save(s, Goal.model_validate(body.model_dump(warnings=False)))


@app.patch("/goals/{id}")
def patch_goal(id: int, body: GoalPatch, s: Session = Depends(get_session)):
    g = get_or_404(s, Goal, id)
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(g, k, v)
    return save(s, g)
