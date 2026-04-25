"""
Database setup — identical pattern to the SSO project.

Uses SQLite for simplicity. The DB file lives next to app.py.
SQLAlchemy handles all the SQL for us.
"""

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# Put agentflow.db in the project root
BASE_DIR = Path(__file__).resolve().parent
DATABASE_URL = f"sqlite:///{BASE_DIR / 'agentflow.db'}"

# Engine = the connection to the database
# check_same_thread=False is needed for SQLite with FastAPI (multiple threads)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# SessionLocal = a factory that creates a new DB session each time
SessionLocal = sessionmaker(bind=engine)


# Base class for all our models (User, SessionRecord, etc.)
class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency: provides a DB session per request, closes it after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
