"""Explicit live write/read and reconnect check using a clearly synthetic habit goal."""
from uuid import uuid4
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlmodel import Session
from app.db import get_engine
from app.models import Goal
from app.config import settings
from app import services as svc

def check():
    engine = get_engine()
    with Session(engine) as s:
        svc.profile(s, required=True)
        row = Goal(owner_id=settings.demo_user_id, title="Synthetic persistence verification",
                   kind="habit", unit="check", start_value=0, current_value=1, target_value=1,
                   status="completed", seed_key="verification:"+str(uuid4()))
        s.add(row)
        s.commit()
        s.refresh(row)
        id = row.id
    engine.dispose()
    with Session(engine) as s:
        assert svc.get(s, Goal, id).current_value == 1
        tables = s.execute(text("""
            SELECT c.relname, c.relrowsecurity
            FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
            WHERE n.nspname='public' AND c.relname IN
            ('user','workoutplan','workout','exercise','workoutsession','workoutset',
             'foodlog','dietplan','goal','chatmessage','proposal','scan','mutation','tooleffect','alembic_version')
        """)).all()
        assert len(tables) == 15 and all(r[1] for r in tables)
        violations = s.execute(text("""
            SELECT grantee, table_name FROM information_schema.table_privileges
            WHERE table_schema='public' AND grantee IN ('anon','authenticated','PUBLIC')
            AND table_name IN ('user','workoutplan','workout','exercise','workoutsession',
            'workoutset','foodlog','dietplan','goal','chatmessage','proposal','scan','mutation','tooleffect','alembic_version')
        """)).all()
        assert not violations
        # Check effective privileges, including inherited/PUBLIC and column-level grants.
        accessible = s.execute(text("""
            SELECT r.role_name, c.relname
            FROM (VALUES ('anon'), ('authenticated')) AS r(role_name)
            CROSS JOIN pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relname IN
            ('user','workoutplan','workout','exercise','workoutsession','workoutset',
             'foodlog','dietplan','goal','chatmessage','proposal','scan','mutation','tooleffect','alembic_version')
            AND (has_table_privilege(r.role_name, c.oid, 'SELECT,INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER')
                 OR has_any_column_privilege(r.role_name, c.oid, 'SELECT,INSERT,UPDATE,REFERENCES'))
        """)).all()
        assert not accessible
        sequences = s.execute(text("""
            SELECT r.role_name, c.relname
            FROM (VALUES ('anon'), ('authenticated')) AS r(role_name)
            CROSS JOIN pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relkind = 'S' AND c.relname IN
            ('user_id_seq','workoutplan_id_seq','workout_id_seq','exercise_id_seq','workoutsession_id_seq',
             'workoutset_id_seq','foodlog_id_seq','dietplan_id_seq','goal_id_seq','chatmessage_id_seq',
             'scan_id_seq','tooleffect_id_seq')
            AND has_sequence_privilege(r.role_name, c.oid, 'USAGE,SELECT,UPDATE')
        """)).all()
        assert not sequences
    print("PASS: synthetic goal", id, "persisted across engine reconnect; all 15 tables use RLS with no client grants.")
    print("The labeled verification goal is retained for inspection. Restart uvicorn and GET /goals to confirm it independently.")

if __name__ == "__main__":
    try:
        check()
    except (SQLAlchemyError, RuntimeError, AssertionError):
        raise SystemExit("Database verification failed. Review local configuration, migration and access controls; secrets are not printed.") from None
