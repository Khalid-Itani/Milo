import os

from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine

load_dotenv()

engine = create_engine(
    f"sqlite:///{os.getenv('FITCOACH_DB', 'fitcoach.db')}",
    connect_args={"check_same_thread": False},
)


def init_db(drop: bool = False):
    from app import models  # noqa: F401  (registers tables)

    if drop:
        SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as s:
        yield s
