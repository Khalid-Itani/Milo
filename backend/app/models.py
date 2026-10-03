from datetime import date as Date, datetime
from typing import Optional

from pydantic import NaiveDatetime
from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = "Agam"
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    age: Optional[int] = None
    sex: Optional[str] = None  # male / female
    kcal_target: int = 2400
    protein_g: int = 150
    carbs_g: int = 250
    fat_g: int = 70
    bmi: Optional[float] = None
    bmi_category: Optional[str] = None


class Workout(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    day_label: str
    notes: str = ""
    status: str = "planned"  # planned / active / done
    started_at: Optional[NaiveDatetime] = None
    finished_at: Optional[NaiveDatetime] = None
    plan_id: Optional[int] = None


class Exercise(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workout_id: int = Field(foreign_key="workout.id")
    name: str
    position: int
    target_sets: int
    target_reps: int
    target_kg: Optional[float] = None


class WorkoutSet(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    exercise_id: int = Field(foreign_key="exercise.id")
    set_index: int
    kg: float = 0
    reps: int = 0
    is_warmup: bool = False
    done: bool = False


class FoodLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: str = Field(default_factory=lambda: Date.today().isoformat())
    meal: str  # breakfast / lunch / dinner / snack
    name: str
    quantity: str = ""
    kcal: float
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0
    source: str = "manual"  # manual / coach


class DietPlan(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    kcal: int
    meals: list = Field(default_factory=list, sa_column=Column(JSON))
    created_at: NaiveDatetime = Field(default_factory=datetime.now)


class Goal(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    kind: str  # strength / body / nutrition / habit
    unit: str = ""
    start_value: float = 0
    current_value: float = 0
    target_value: float
    deadline: Optional[Date] = None
    status: str = "active"  # active / completed


class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    role: str
    content: str
    cards: list = Field(default_factory=list, sa_column=Column(JSON))
    created_at: NaiveDatetime = Field(default_factory=datetime.now)
