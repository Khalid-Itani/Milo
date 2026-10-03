"""Coach tools: JSON schemas for the model + implementations that write to the DB and return a Card."""
from datetime import date

from sqlmodel import Session, select

from app.models import DietPlan, Exercise, FoodLog, Goal, Workout, WorkoutSet
from app.today import build_today, next_workout

MACROS = {k: {"type": "number"} for k in ("kcal", "protein_g", "carbs_g", "fat_g")}

TOOLS = [
    {
        "name": "create_workout_plan",
        "description": "Save a multi-day training plan. Each workout is added to the Train tab.",
        "input_schema": {
            "type": "object",
            "properties": {
                "plan_name": {"type": "string"},
                "weeks": {"type": "integer"},
                "workouts": {"type": "array", "items": {
                    "type": "object",
                    "properties": {
                        "day_label": {"type": "string", "description": "MON, TUE, ..."},
                        "name": {"type": "string"},
                        "exercises": {"type": "array", "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "sets": {"type": "integer"},
                                "reps": {"type": "integer"},
                                "kg": {"type": "number"},
                            },
                            "required": ["name", "sets", "reps"],
                        }},
                    },
                    "required": ["day_label", "name", "exercises"],
                }},
            },
            "required": ["plan_name", "weeks", "workouts"],
        },
    },
    {
        "name": "log_workout_set",
        "description": "Log a completed set for an exercise in the active (or next) workout.",
        "input_schema": {
            "type": "object",
            "properties": {"exercise_name": {"type": "string"}, "kg": {"type": "number"}, "reps": {"type": "integer"}},
            "required": ["exercise_name", "kg", "reps"],
        },
    },
    {
        "name": "log_food",
        "description": "Log a food item the user ate today.",
        "input_schema": {
            "type": "object",
            "properties": {
                "meal": {"type": "string", "enum": ["breakfast", "lunch", "dinner", "snack"]},
                "name": {"type": "string"},
                "quantity": {"type": "string"},
                **MACROS,
            },
            "required": ["meal", "name", "quantity", "kcal", "protein_g", "carbs_g", "fat_g"],
        },
    },
    {
        "name": "create_diet_plan",
        "description": "Save a day of meals as a diet plan.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "kcal": {"type": "integer"},
                "meals": {"type": "array", "items": {
                    "type": "object",
                    "properties": {"meal": {"type": "string"}, "name": {"type": "string"}, **MACROS},
                    "required": ["meal", "name", "kcal", "protein_g", "carbs_g", "fat_g"],
                }},
            },
            "required": ["name", "kcal", "meals"],
        },
    },
    {
        "name": "set_goal",
        "description": "Save a goal for the user.",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "kind": {"type": "string", "enum": ["strength", "body", "nutrition", "habit"]},
                "unit": {"type": "string"},
                "start_value": {"type": "number"},
                "target_value": {"type": "number"},
                "deadline": {"type": "string", "description": "YYYY-MM-DD"},
            },
            "required": ["title", "kind", "unit", "start_value", "target_value"],
        },
    },
    {
        "name": "get_today",
        "description": "Get today's calories, macros, BMI, weekly training and next workout.",
        "input_schema": {"type": "object", "properties": {}},
    },
]


def create_workout_plan(s: Session, plan_name: str, weeks: int, workouts: list) -> tuple[dict, dict]:
    plan_id = (s.exec(select(Workout.plan_id).order_by(Workout.plan_id.desc())).first() or 0) + 1
    out = []
    for w in workouts:
        row = Workout(name=w["name"], day_label=w["day_label"].upper()[:3], plan_id=plan_id)
        s.add(row)
        s.flush()
        for pos, e in enumerate(w["exercises"]):
            ex = Exercise(workout_id=row.id, name=e["name"], position=pos, target_sets=e["sets"], target_reps=e["reps"], target_kg=e.get("kg"))
            s.add(ex)
            s.flush()
            for i in range(e["sets"]):
                s.add(WorkoutSet(exercise_id=ex.id, set_index=i, kg=e.get("kg") or 0, reps=e["reps"]))
        out.append({"id": row.id, "day_label": row.day_label, "name": row.name,
                    "summary": " · ".join(e["name"] for e in w["exercises"])})
    s.commit()
    data = {"plan_name": plan_name, "weeks": weeks, "workouts": out}
    return data, {"type": "workout_plan", "data": data}


def log_workout_set(s: Session, exercise_name: str, kg: float, reps: int) -> tuple[dict, dict]:
    w = next_workout(s)
    ex = w and s.exec(select(Exercise).where(Exercise.workout_id == w.id, Exercise.name.ilike(f"%{exercise_name}%"))).first()
    if not ex:
        raise ValueError(f"No exercise matching '{exercise_name}' in the current workout")
    sets = s.exec(select(WorkoutSet).where(WorkoutSet.exercise_id == ex.id).order_by(WorkoutSet.set_index)).all()
    target = next((x for x in sets if not x.done), None) or WorkoutSet(exercise_id=ex.id, set_index=len(sets))
    target.kg, target.reps, target.done = kg, reps, True
    s.add(target)
    s.commit()
    data = {"exercise": ex.name, "kg": kg, "reps": reps}
    return data, {"type": "set_logged", "data": data}


def log_food(s: Session, **fields) -> tuple[dict, dict]:
    f = FoodLog(date=date.today().isoformat(), source="coach", **fields)
    s.add(f)
    s.commit()
    s.refresh(f)
    left = build_today(s)
    data = {k: getattr(f, k) for k in ("id", "meal", "name", "kcal", "protein_g", "carbs_g", "fat_g")}
    return data | {"kcal_left": left["kcal"]["left"]}, {"type": "food_logged", "data": data}


def create_diet_plan(s: Session, name: str, kcal: int, meals: list) -> tuple[dict, dict]:
    p = DietPlan(name=name, kcal=kcal, meals=meals)
    s.add(p)
    s.commit()
    s.refresh(p)
    data = {"id": p.id, "name": name, "kcal": kcal, "meals": meals}
    return data, {"type": "diet_plan", "data": data}


def set_goal(s: Session, deadline: str | None = None, **fields) -> tuple[dict, dict]:
    g = Goal(current_value=fields["start_value"], deadline=date.fromisoformat(deadline) if deadline else None, **fields)
    s.add(g)
    s.commit()
    s.refresh(g)
    data = {"id": g.id, "title": g.title, "target_value": g.target_value, "unit": g.unit, "deadline": deadline}
    return data, {"type": "goal_set", "data": data}


def get_today(s: Session) -> tuple[dict, None]:
    return build_today(s), None


IMPLS = {f.__name__: f for f in (create_workout_plan, log_workout_set, log_food, create_diet_plan, set_goal, get_today)}


def execute(s: Session, name: str, args: dict) -> tuple[dict, dict | None]:
    return IMPLS[name](s, **args)
