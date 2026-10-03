"""Drop and recreate the DB with mockup data. `--fresh` leaves the profile empty to demo onboarding."""
import sys
from datetime import date, datetime, timedelta

from sqlmodel import Session

from app.db import engine, init_db
from app.models import ChatMessage, Exercise, FoodLog, Goal, User, Workout, WorkoutSet

PLAN = [
    ("MON", "Upper A — Strength", "done", [("Bench Press", 5, 5, 85), ("Barbell Row", 4, 8, 70), ("Overhead Press", 3, 8, 45), ("Pull-up", 3, 8, None)]),
    ("TUE", "Lower A", "done", [("Back Squat", 5, 5, 100), ("Romanian Deadlift", 3, 8, 80), ("Leg Press", 3, 12, 160), ("Calf Raise", 3, 15, 60)]),
    ("THU", "Lower B", "done", [("Deadlift", 4, 5, 130), ("Front Squat", 3, 8, 70), ("Walking Lunge", 3, 12, 20), ("Leg Curl", 3, 12, 40)]),
    ("SAT", "Upper B — Volume", "planned", [("Bench Press", 4, 8, 75), ("Incline DB Press", 3, 10, 30), ("Cable Fly", 3, 12, 17.5), ("Lateral Raise", 3, 15, 10)]),
]
DAY_OFFSET = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6}

FOOD = [  # meal, name, quantity, kcal, P, C, F, source
    ("breakfast", "Greek yogurt 2%", "250 g", 183, 25, 10, 5, "manual"),
    ("breakfast", "Granola", "45 g", 205, 5, 28, 7, "manual"),
    ("breakfast", "Blueberries", "1 cup", 84, 1, 21, 0, "manual"),
    ("breakfast", "Latte", "12 oz", 58, 4, 6, 1, "manual"),
    ("lunch", "Chicken burrito bowl, guacamole", "1 bowl", 680, 42, 71, 24, "coach"),
    ("snack", "Protein shake", "1 scoop + milk", 210, 42, 6, 3, "manual"),
    ("snack", "Banana", "1 medium", 105, 1, 27, 0, "manual"),
    ("snack", "Peanut butter", "1 tbsp", 95, 4, 3, 8, "manual"),
]


def seed(fresh: bool = False):
    init_db(drop=True)
    today = date.today()
    monday = datetime.combine(today - timedelta(days=today.weekday()), datetime.min.time())
    with Session(engine) as s:
        profile = {} if fresh else dict(height_cm=180, weight_kg=74.6, age=21, sex="male", bmi=23.0, bmi_category="Normal")
        s.add(User(id=1, name="Agam", kcal_target=2450, protein_g=160, carbs_g=260, fat_g=75, **profile))

        for day, name, status, exercises in PLAN:
            w = Workout(name=name, day_label=day, status=status, plan_id=1)
            if status == "done":
                w.started_at = monday + timedelta(days=DAY_OFFSET[day], hours=18)
                w.finished_at = w.started_at + timedelta(minutes=55)
            s.add(w)
            s.flush()
            for pos, (ex_name, sets, reps, kg) in enumerate(exercises):
                e = Exercise(workout_id=w.id, name=ex_name, position=pos, target_sets=sets, target_reps=reps, target_kg=kg)
                s.add(e)
                s.flush()
                for i in range(sets):
                    s.add(WorkoutSet(exercise_id=e.id, set_index=i, kg=kg or 0, reps=reps, done=status == "done"))

        for meal, name, qty, kcal, p, c, f, src in FOOD:
            s.add(FoodLog(date=today.isoformat(), meal=meal, name=name, quantity=qty, kcal=kcal, protein_g=p, carbs_g=c, fat_g=f, source=src))

        s.add_all([
            Goal(title="Bench press 100 kg", kind="strength", unit="kg", start_value=85, current_value=95, target_value=100, deadline=date(today.year, 12, 15)),
            Goal(title="Reach 72 kg", kind="body", unit="kg", start_value=76.8, current_value=74.6, target_value=72, deadline=date(today.year + (today.month > 1), 1, 31)),
            Goal(title="160 g protein daily", kind="nutrition", unit="g", start_value=0, current_value=124, target_value=160),
            Goal(title="Train 4× a week", kind="habit", unit="sessions", start_value=0, current_value=3, target_value=4),
            ChatMessage(role="assistant", content="Hey Agam. Tell me what you ate or what you want to train, and I'll log and plan it."),
        ])
        s.commit()


if __name__ == "__main__":
    seed(fresh="--fresh" in sys.argv)
    print("seeded")
