from datetime import date, datetime, time, timedelta

from sqlmodel import Session, select

from app.models import Exercise, FoodLog, User, Workout

SESSIONS_TARGET = 4  # ponytail: fixed weekly target, read from the habit goal if it needs to vary


def food_totals(s: Session, day: str) -> dict:
    items = s.exec(select(FoodLog).where(FoodLog.date == day)).all()
    return {k: round(sum(getattr(f, k) for f in items)) for k in ("kcal", "protein_g", "carbs_g", "fat_g")}


def next_workout(s: Session) -> Workout | None:
    for status in ("active", "planned"):
        w = s.exec(select(Workout).where(Workout.status == status).order_by(Workout.id)).first()
        if w:
            return w
    return None


def build_today(s: Session) -> dict:
    u = s.get(User, 1)
    today = date.today()
    t = food_totals(s, today.isoformat())
    kcal_left = u.kcal_target - t["kcal"]
    p_left = u.protein_g - t["protein_g"]

    monday = datetime.combine(today - timedelta(days=today.weekday()), time.min)
    done = s.exec(select(Workout).where(Workout.status == "done", Workout.finished_at >= monday)).all()
    days = [False] * 7
    for w in done:
        days[w.finished_at.weekday()] = True

    nxt = next_workout(s)
    next_out = None
    if nxt:
        exs = s.exec(select(Exercise).where(Exercise.workout_id == nxt.id)).all()
        next_out = {
            "id": nxt.id,
            "name": nxt.name,
            "exercise_count": len(exs),
            "est_minutes": round(sum(e.target_sets for e in exs) * 4.25),  # ~4 min per working set
        }

    if p_left > 20 and kcal_left > 400:
        tip = f"{p_left} g protein to go. A salmon rice bowl for dinner closes it at about 780 kcal."
    elif kcal_left < 0:
        tip = f"You're {-kcal_left} kcal over today. Keep dinner light and protein-first."
    elif p_left > 0:
        tip = f"{p_left} g protein and {kcal_left} kcal left. A shake or Greek yogurt closes it."
    else:
        tip = f"Protein target hit. {kcal_left} kcal left for the day."

    return {
        "date": today.isoformat(),
        "kcal": {"target": u.kcal_target, "eaten": t["kcal"], "left": kcal_left},
        "macros": {
            "protein": {"eaten": t["protein_g"], "target": u.protein_g},
            "carbs": {"eaten": t["carbs_g"], "target": u.carbs_g},
            "fat": {"eaten": t["fat_g"], "target": u.fat_g},
        },
        "bmi": {"value": u.bmi, "category": u.bmi_category},
        "weight_kg": u.weight_kg,
        "week": {"sessions_done": len(done), "sessions_target": SESSIONS_TARGET, "days": days},
        "next_workout": next_out,
        "coach_tip": tip,
    }
