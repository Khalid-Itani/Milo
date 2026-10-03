from pydantic import BaseModel
from sqlmodel import Session, select

from app.models import Exercise, Workout, WorkoutSet


class ProfileIn(BaseModel):
    height_cm: float
    weight_kg: float
    age: int
    sex: str


class ChatIn(BaseModel):
    message: str


class SetIn(BaseModel):
    kg: float
    reps: int
    is_warmup: bool = False


class SetPatch(BaseModel):
    kg: float | None = None
    reps: int | None = None
    done: bool | None = None


class GoalPatch(BaseModel):
    current_value: float | None = None
    status: str | None = None


def workout_out(s: Session, w: Workout) -> dict:
    exercises = s.exec(select(Exercise).where(Exercise.workout_id == w.id).order_by(Exercise.position)).all()
    return w.model_dump() | {
        "exercises": [
            e.model_dump() | {
                "sets": [x.model_dump() for x in s.exec(
                    select(WorkoutSet).where(WorkoutSet.exercise_id == e.id).order_by(WorkoutSet.set_index)
                ).all()]
            }
            for e in exercises
        ]
    }
