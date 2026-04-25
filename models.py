"""
Database models — simplified version of the SSO project.

We only need two tables for Google auth:
  - User: stores who logged in (email, name)
  - SessionRecord: tracks active sessions (maps cookie → user)
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Boolean

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    picture = Column(String, nullable=True)          # Google profile picture URL
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SessionRecord(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    session_token = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(Integer, nullable=False)
    expires_at = Column(DateTime, nullable=False)
