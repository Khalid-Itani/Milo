"""Initial Milo schema. Frozen definitions; never import evolving application metadata."""
from alembic import op
import sqlalchemy as sa

revision = "0001_milo"
down_revision = None
branch_labels = None
depends_on = None


def c(name, type_, nullable=False, **kw):
    return sa.Column(name, type_, nullable=nullable, **kw)


def owned_table(name, columns, constraints=(), indexes=()):
    op.create_table(name,
        c("id", sa.Integer(), primary_key=True) if name not in ("proposal", "mutation") else c("id", sa.String(), primary_key=True),
        c("owner_id", sa.Integer()), c("seed_key", sa.String(), nullable=True),
        *columns,
        sa.ForeignKeyConstraint(["owner_id"], ["user.id"]),
        sa.UniqueConstraint("seed_key", name="uq_"+name+"_seed_key"), *constraints)
    op.create_index("ix_"+name+"_owner_id", name, ["owner_id"])
    for field in indexes:
        op.create_index("ix_"+name+"_"+field, name, [field])


def upgrade():
    op.create_table("user",
        c("id", sa.Integer(), primary_key=True), c("name", sa.String()),
        c("height_cm", sa.Float(), nullable=True), c("weight_kg", sa.Float(), nullable=True),
        c("age", sa.Integer(), nullable=True), c("sex", sa.String(), nullable=True),
        c("kcal_target", sa.Integer(), nullable=True), c("protein_g", sa.Integer(), nullable=True),
        c("carbs_g", sa.Integer(), nullable=True), c("fat_g", sa.Integer(), nullable=True),
        c("targets_source", sa.String(), nullable=True),
        c("bmi", sa.Float(), nullable=True), c("bmi_category", sa.String(), nullable=True),
        c("preferences", sa.JSON()), c("allergies", sa.JSON()), c("equipment", sa.JSON()),
        c("experience", sa.String()), c("available_days", sa.JSON()), c("goals_context", sa.String()),
        c("timezone", sa.String()), c("scan_storage_consent", sa.Boolean()),
        c("scan_ai_sharing_consent", sa.Boolean()),
        sa.CheckConstraint("height_cm IS NULL OR height_cm > 0", name="ck_positive_height"),
        sa.CheckConstraint("weight_kg IS NULL OR weight_kg > 0", name="ck_positive_weight"),
        sa.CheckConstraint("kcal_target IS NULL OR kcal_target > 0", name="ck_positive_target"))
    owned_table("workoutplan", [c("name", sa.String()), c("weeks", sa.Integer()), c("status", sa.String()),
        c("created_at", sa.DateTime(timezone=True))],
        [sa.CheckConstraint("weeks > 0", name="ck_plan_weeks"),
         sa.CheckConstraint("status IN ('pending','active','archived')", name="ck_plan_status")])
    owned_table("workout", [c("name", sa.String()), c("day_label", sa.String()), c("notes", sa.String()), c("plan_id", sa.Integer())],
        [sa.ForeignKeyConstraint(["plan_id"], ["workoutplan.id"]),
         sa.CheckConstraint("day_label IN ('MON','TUE','WED','THU','FRI','SAT','SUN')", name="ck_workout_day")], ["plan_id"])
    owned_table("exercise", [c("workout_id", sa.Integer()), c("name", sa.String()), c("position", sa.Integer()),
        c("target_sets", sa.Integer()), c("target_reps", sa.Integer()), c("target_kg", sa.Float(), nullable=True)],
        [sa.ForeignKeyConstraint(["workout_id"], ["workout.id"]),
         sa.CheckConstraint("target_sets > 0 AND target_reps > 0", name="ck_exercise_targets")], ["workout_id"])
    owned_table("workoutsession", [c("workout_id", sa.Integer()), c("status", sa.String()), c("source", sa.String()),
        c("active_slot", sa.Integer(), nullable=True), c("started_at", sa.DateTime(timezone=True), nullable=True),
        c("finished_at", sa.DateTime(timezone=True), nullable=True)],
        [sa.ForeignKeyConstraint(["workout_id"], ["workout.id"]),
         sa.UniqueConstraint("owner_id", "active_slot", name="uq_active_session"),
         sa.CheckConstraint("status IN ('prepared','active','completed')", name="ck_session_status"),
         sa.CheckConstraint("(status = 'active' AND active_slot = 1) OR (status <> 'active' AND active_slot IS NULL)", name="ck_session_slot"),
         sa.CheckConstraint("status <> 'completed' OR (started_at IS NOT NULL AND finished_at IS NOT NULL)", name="ck_completed_dates")],
        ["workout_id", "finished_at"])
    owned_table("workoutset", [c("exercise_id", sa.Integer()), c("session_id", sa.Integer()), c("set_index", sa.Integer()),
        c("kg", sa.Float()), c("reps", sa.Integer()), c("is_warmup", sa.Boolean()), c("done", sa.Boolean())],
        [sa.ForeignKeyConstraint(["exercise_id"], ["exercise.id"]), sa.ForeignKeyConstraint(["session_id"], ["workoutsession.id"]),
         sa.UniqueConstraint("session_id", "exercise_id", "set_index", name="uq_session_set"),
         sa.CheckConstraint("kg >= 0 AND reps >= 0 AND set_index >= 0", name="ck_set_values")], ["exercise_id", "session_id"])
    owned_table("foodlog", [c("date", sa.String()), c("captured_at", sa.DateTime(timezone=True)),
        c("meal", sa.String()), c("name", sa.String()), c("quantity", sa.String()), c("kcal", sa.Float()),
        c("protein_g", sa.Float()), c("carbs_g", sa.Float()), c("fat_g", sa.Float()), c("source", sa.String()),
        c("nutrition_provenance", sa.String()), c("is_estimate", sa.Boolean())],
        [sa.CheckConstraint("meal IN ('breakfast','lunch','dinner','snack')", name="ck_food_meal"),
         sa.CheckConstraint("kcal >= 0 AND protein_g >= 0 AND carbs_g >= 0 AND fat_g >= 0", name="ck_food_nutrition")],
        ["date", "captured_at"])
    owned_table("dietplan", [c("name", sa.String()), c("kcal", sa.Integer()), c("meals", sa.JSON()),
        c("status", sa.String()), c("created_at", sa.DateTime(timezone=True))],
        [sa.CheckConstraint("status IN ('pending','active','archived')", name="ck_diet_status")])
    owned_table("goal", [c("title", sa.String()), c("kind", sa.String()), c("unit", sa.String()),
        c("start_value", sa.Float()), c("current_value", sa.Float()), c("target_value", sa.Float()),
        c("deadline", sa.Date(), nullable=True), c("status", sa.String()), c("progress_source", sa.String())],
        [sa.CheckConstraint("kind IN ('strength','body','nutrition','habit')", name="ck_goal_kind"),
         sa.CheckConstraint("status IN ('active','completed')", name="ck_goal_status"),
         sa.CheckConstraint("progress_source IN ('explicit','weekly_sessions','daily_protein')", name="ck_goal_progress")])
    owned_table("chatmessage", [c("role", sa.String()), c("content", sa.String()), c("cards", sa.JSON()),
        c("conversation_id", sa.String(), nullable=True), c("request_ref", sa.String(), nullable=True),
        c("created_at", sa.DateTime(timezone=True))], indexes=["conversation_id", "request_ref"])
    owned_table("proposal", [c("kind", sa.String()), c("resource_id", sa.Integer()),
        c("status", sa.String()), c("card", sa.JSON()), c("created_at", sa.DateTime(timezone=True))])
    owned_table("scan", [c("client_scan_id", sa.String()), c("payload_hash", sa.String()),
        c("captured_at", sa.DateTime(timezone=True)), c("metrics", sa.JSON()), c("source", sa.String()),
        c("source_metadata", sa.JSON()), c("verification", sa.String())],
        [sa.UniqueConstraint("owner_id", "client_scan_id", name="uq_client_scan")], ["captured_at"])
    owned_table("mutation", [c("key", sa.String()), c("fingerprint", sa.String()), c("state", sa.String()),
        c("lease_token", sa.String()), c("lease_until", sa.DateTime(timezone=True)), c("result", sa.JSON(), nullable=True),
        c("progress", sa.JSON()), c("created_at", sa.DateTime(timezone=True))],
        [sa.UniqueConstraint("owner_id", "key", name="uq_mutation_key")])
    owned_table("tooleffect", [c("mutation_id", sa.String()), c("fingerprint", sa.String()),
        c("result", sa.JSON()), c("card", sa.JSON(), nullable=True)],
        [sa.ForeignKeyConstraint(["mutation_id"], ["mutation.id"]),
         sa.UniqueConstraint("mutation_id", "fingerprint", name="uq_tool_effect")], ["mutation_id"])
    if op.get_bind().dialect.name == "postgresql":
        # Explicit deny: no client policies or grants. Do not touch unrelated tables/functions.
        tables = ("user", "workoutplan", "workout", "exercise", "workoutsession", "workoutset",
                  "foodlog", "dietplan", "goal", "chatmessage", "proposal", "scan", "mutation", "tooleffect", "alembic_version")
        for table in tables:
            op.execute(f'ALTER TABLE public."{table}" ENABLE ROW LEVEL SECURITY')
            op.execute(f'REVOKE ALL ON TABLE public."{table}" FROM PUBLIC, anon, authenticated')
        for table in tables:
            if table not in ("proposal", "mutation", "alembic_version"):
                op.execute(f'REVOKE ALL ON SEQUENCE public."{table}_id_seq" FROM PUBLIC, anon, authenticated')


def downgrade():
    raise RuntimeError("Destructive downgrade is disabled. Restore from a reviewed backup instead.")
