"""Explicit synthetic demo upsert. Never delete data, create schema, or seed on startup."""
import argparse
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo
from sqlmodel import select
from sqlalchemy.exc import SQLAlchemyError

from app import db, services as svc
from app.config import settings
from app.models import User, WorkoutPlan, Workout, Exercise, WorkoutSession, FoodLog, Goal, ChatMessage
from app.schemas import ProfileIn

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


def seed(fresh=False, factory=None):
    factory = factory or db.session_factory
    with factory() as s:
        with s.begin():
            svc.guard_owner(s)
            u = s.get(User, settings.demo_user_id)
            if not u:
                svc.save_profile(s, ProfileIn(**({} if fresh else dict(
                    name="Agam (synthetic demo)", height_cm=180, weight_kg=74.6, age=21, sex="male",
                    kcal_target=2450, protein_g=160, carbs_g=260, fat_g=75,
                    available_days=["MON", "TUE", "THU", "SAT"]))))
                u = svc.profile(s, required=True)
                if not fresh:
                    u.targets_source = "synthetic_demo"
                    s.add(u)
            if fresh:
                return
            def upsert(model, label, **data):
                key = f"milo_demo_v1:{settings.demo_user_id}:{label}"
                row = s.exec(svc.owned(model).where(model.seed_key == key)).first()
                if row:
                    return row, False
                row = model(owner_id=settings.demo_user_id, seed_key=key, **data)
                s.add(row)
                s.flush()
                return row, True
            plan, _ = upsert(WorkoutPlan, "plan", name="Upper / Lower · 4 days (synthetic)", weeks=8)
            day = svc.local_day(u)
            monday = day-timedelta(days=day.weekday())
            for label, name, status, specs in PLAN:
                w, created = upsert(Workout, "workout:"+label, name=name, day_label=label,
                                    notes="Synthetic demo template", plan_id=plan.id)
                for pos, (ex_name, sets, reps, kg) in enumerate(specs):
                    upsert(Exercise, f"exercise:{label}:{pos}", workout_id=w.id, name=ex_name, position=pos,
                           target_sets=sets, target_reps=reps, target_kg=kg)
                if created:
                    current = svc.prepare_session(s, w)
                    current.source = "synthetic"
                    current.seed_key = f"milo_demo_v1:{settings.demo_user_id}:session:{label}"
                    # Only seed dated completions which have already occurred, never future sessions.
                    completed_day = monday+timedelta(days=DAY_OFFSET[label])
                    if status == "done" and completed_day <= day:
                        end = datetime.combine(completed_day, time(12), ZoneInfo(u.timezone)).astimezone(timezone.utc)
                        current.status, current.started_at, current.finished_at = "completed", end-timedelta(minutes=55), end
                        for ex in svc.exercises(s, w.id):
                            for row in svc.session_sets(s, current.id, ex.id):
                                row.done = True
                                s.add(row)
                    s.add(current)
            for i, (meal, name, qty, kcal, p, c, f, src) in enumerate(FOOD):
                captured = datetime.combine(day, time(12), ZoneInfo(u.timezone)).astimezone(timezone.utc)
                upsert(FoodLog, "food:"+str(i), date=day.isoformat(), captured_at=captured, meal=meal,
                       name=name, quantity=qty, kcal=kcal, protein_g=p, carbs_g=c, fat_g=f,
                       source="synthetic", nutrition_provenance="synthetic", is_estimate=True)
            upsert(Goal, "strength_goal", title="Bench press 100 kg (synthetic)", kind="strength",
                   unit="kg", start_value=85, current_value=95, target_value=100)
            upsert(Goal, "body_goal", title="Reach 72 kg (synthetic)", kind="body", unit="kg",
                   start_value=76.8, current_value=74.6, target_value=72)
            upsert(Goal, "protein_goal", title="160 g protein daily (synthetic)", kind="nutrition",
                   unit="g", target_value=160, progress_source="daily_protein")
            upsert(Goal, "frequency_goal", title="Train 4× a week (synthetic)", kind="habit",
                   unit="sessions", target_value=4, progress_source="weekly_sessions")
            upsert(ChatMessage, "welcome", role="assistant",
                   content="This profile and initial records are synthetic demo data. Tell me what you ate or want to train.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fresh", action="store_true", help="Create an empty profile only if absent; never clear existing data")
    args = parser.parse_args()
    try:
        seed(fresh=args.fresh)
    except (SQLAlchemyError, RuntimeError):
        raise SystemExit("Seed failed. Check server configuration and apply migrations; details are not printed.") from None
    print("Synthetic demo seed upsert complete; existing records preserved.")
