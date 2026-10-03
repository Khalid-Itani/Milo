from datetime import date as Date, datetime, timezone
from typing import Optional
from sqlalchemy import JSON, Column, DateTime, UniqueConstraint
from sqlmodel import Field, SQLModel

def utcnow():
    return datetime.now(timezone.utc)

def json_list():
    return Field(default_factory=list, sa_column=Column(JSON, nullable=False))

def timestamp():
    return Field(default_factory=utcnow, sa_column=Column(DateTime(timezone=True), nullable=False))

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = "Demo user"
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    age: Optional[int] = None
    sex: Optional[str] = None
    kcal_target: Optional[int] = None
    protein_g: Optional[int] = None
    carbs_g: Optional[int] = None
    fat_g: Optional[int] = None
    targets_source: Optional[str] = None
    bmi: Optional[float] = None
    bmi_category: Optional[str] = None
    preferences: list = json_list()
    allergies: list = json_list()
    equipment: list = json_list()
    experience: str = "unspecified"
    available_days: list = json_list()
    goals_context: str = ""
    timezone: str = "America/New_York"
    scan_storage_consent: bool = False
    scan_ai_sharing_consent: bool = False

class Owned(SQLModel):
    owner_id: int = Field(foreign_key="user.id", index=True)
    seed_key: Optional[str] = Field(default=None, unique=True)

class WorkoutPlan(Owned, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    weeks: int
    status: str = "active"
    created_at: datetime = timestamp()

class Workout(Owned, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    day_label: str
    notes: str = ""
    plan_id: int = Field(foreign_key="workoutplan.id", index=True)

class Exercise(Owned, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    workout_id: int = Field(foreign_key="workout.id", index=True)
    name: str
    position: int
    target_sets: int
    target_reps: int
    target_kg: Optional[float] = None

class WorkoutSession(Owned, table=True):
    __table_args__ = (UniqueConstraint("owner_id", "active_slot", name="uq_active_session"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    workout_id: int = Field(foreign_key="workout.id", index=True)
    status: str = "prepared"
    source: str = "manual"
    active_slot: Optional[int] = None
    started_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True)))
    finished_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime(timezone=True), index=True))

class WorkoutSet(Owned, table=True):
    __table_args__ = (UniqueConstraint("session_id", "exercise_id", "set_index", name="uq_session_set"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    exercise_id: int = Field(foreign_key="exercise.id", index=True)
    session_id: int = Field(foreign_key="workoutsession.id", index=True)
    set_index: int
    kg: float = 0
    reps: int = 0
    is_warmup: bool = False
    done: bool = False

class FoodLog(Owned, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    date: str = Field(index=True)
    captured_at: datetime = timestamp()
    meal: str
    name: str
    quantity: str = ""
    kcal: float
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0
    source: str = "manual"
    nutrition_provenance: str = "user_estimate"
    is_estimate: bool = True

class DietPlan(Owned, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    kcal: int
    meals: list = json_list()
    status: str = "active"
    created_at: datetime = timestamp()

class Goal(Owned, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    kind: str
    unit: str = ""
    start_value: float = 0
    current_value: float = 0
    target_value: float
    deadline: Optional[Date] = None
    status: str = "active"
    progress_source: str = "explicit"

class ChatMessage(Owned, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    role: str
    content: str
    cards: list = json_list()
    conversation_id: Optional[str] = Field(default=None, index=True)
    request_ref: Optional[str] = Field(default=None, index=True)
    created_at: datetime = timestamp()

class Proposal(Owned, table=True):
    id: str = Field(primary_key=True)
    kind: str
    resource_id: int
    status: str = "pending"
    card: dict = Field(sa_column=Column(JSON, nullable=False))
    created_at: datetime = timestamp()

class Scan(Owned, table=True):
    __table_args__ = (UniqueConstraint("owner_id", "client_scan_id", name="uq_client_scan"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    client_scan_id: str
    payload_hash: str
    captured_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False, index=True))
    metrics: list = json_list()
    source: str
    source_metadata: dict = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    verification: str = "client-reported"

class Mutation(Owned, table=True):
    __table_args__ = (UniqueConstraint("owner_id", "key", name="uq_mutation_key"),)
    id: str = Field(primary_key=True)
    key: str
    fingerprint: str
    state: str = "running"
    lease_token: str
    lease_until: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    result: Optional[dict] = Field(default=None, sa_column=Column(JSON))
    progress: dict = Field(default_factory=dict, sa_column=Column(JSON, nullable=False))
    created_at: datetime = timestamp()

class ToolEffect(Owned, table=True):
    __table_args__ = (UniqueConstraint("mutation_id", "fingerprint", name="uq_tool_effect"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    mutation_id: str = Field(foreign_key="mutation.id", index=True)
    fingerprint: str
    result: dict = Field(sa_column=Column(JSON, nullable=False))
    card: Optional[dict] = Field(default=None, sa_column=Column(JSON))
