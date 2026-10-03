"""Lazy Postgres engine: no connections, schema creation or seed on import."""
from functools import lru_cache
from sqlalchemy.engine import make_url
from sqlmodel import Session, create_engine
from app.config import settings

@lru_cache
def get_engine():
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not configured")
    try:
        url = make_url(settings.database_url)
        if url.drivername not in ("postgresql", "postgresql+psycopg"):
            raise ValueError()
        if url.query.get("sslmode") not in ("require", "verify-ca", "verify-full"):
            raise ValueError()
        url = url.set(drivername="postgresql+psycopg")
    except Exception:
        raise RuntimeError("DATABASE_URL must use PostgreSQL and sslmode=require or stronger") from None
    return create_engine(url, pool_size=3, max_overflow=2, pool_timeout=10,
                         pool_pre_ping=True, pool_recycle=600, hide_parameters=True,
                         connect_args={"connect_timeout": 10, "prepare_threshold": None})

def session_factory():
    return Session(get_engine(), expire_on_commit=False)


def close_engine():
    """Dispose an existing pool on shutdown without opening an unconfigured database."""
    if get_engine.cache_info().currsize:
        get_engine().dispose()
        get_engine.cache_clear()
