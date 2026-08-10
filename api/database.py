import os
import logging

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger("familysecure_backend")

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./familysecure.db")

_connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    import api.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    logger.info(f"Database siap ({DATABASE_URL.split('://')[0]}).")
