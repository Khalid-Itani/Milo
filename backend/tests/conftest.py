"""Explicit isolated SQLite test adapter. Production can only construct Postgres engines."""
from datetime import datetime, timezone
import pytest
import httpx
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlmodel import Session, SQLModel, create_engine
from app import services as svc
from app.config import settings
from app.main import app
from app.seed import seed
from agent import coach


def test_engine(path):
    engine = create_engine("sqlite:///"+str(path), connect_args={"check_same_thread": False, "timeout": 10})
    @event.listens_for(engine, "connect")
    def configure(connection, record):
        connection.isolation_level = None
        connection.execute("PRAGMA foreign_keys=ON")
    @event.listens_for(engine, "begin")
    def begin(connection):
        # Explicit test-only equivalent of serializing short owner transactions.
        connection.exec_driver_sql("BEGIN IMMEDIATE")
    return engine


@pytest.fixture
def env(tmp_path, monkeypatch):
    engine = test_engine(tmp_path/"isolated.db")
    SQLModel.metadata.create_all(engine)  # allowed only in this explicit test adapter
    factory = lambda: Session(engine, expire_on_commit=False)
    monkeypatch.setattr(app.state, "session_factory", factory)
    monkeypatch.setattr(settings, "demo_api_token", "offline-demo-token")
    monkeypatch.setattr(settings, "demo_user_id", 1)
    monkeypatch.setattr(settings, "anthropic_api_key", "offline-provider-key")
    monkeypatch.setattr(svc, "utcnow", lambda: datetime(2026, 10, 3, 16, tzinfo=timezone.utc))
    def network_forbidden(*args, **kwargs):
        raise AssertionError("Offline test attempted a live call")
    monkeypatch.setattr(httpx.HTTPTransport, "handle_request", network_forbidden)
    monkeypatch.setattr(coach, "create_message", network_forbidden)
    seed(factory=factory)
    with TestClient(app, headers={"Authorization": "Bearer offline-demo-token"}) as client:
        yield client, factory, engine
    engine.dispose()


@pytest.fixture
def c(env):
    return env[0]
