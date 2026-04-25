"""
Auth dependencies — the GATEKEEPER.

Any route that adds `user = Depends(get_current_user)` will:
  1. Read the session_token cookie
  2. Look it up in the database
  3. Check if it's expired
  4. Return the User object if valid
  5. Raise 401 if anything fails

This is the same pattern as sso-project/app/auth/dependencies.py
"""

from datetime import datetime

from fastapi import Request, HTTPException, Depends
from sqlalchemy.orm import Session as DBSession

from database import get_db
from models import User, SessionRecord


def get_current_user(request: Request, db: DBSession = Depends(get_db)) -> User:
    """
    FastAPI dependency that protects routes.

    Usage:
        @app.get("/protected")
        def my_route(user: User = Depends(get_current_user)):
            return {"hello": user.name}
    """

    # Step 1: Read the cookie
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(401, "Not logged in — no session cookie")

    # Step 2: Look up session in DB
    session = db.query(SessionRecord).filter(
        SessionRecord.session_token == token
    ).first()
    if not session:
        raise HTTPException(401, "Invalid session")

    # Step 3: Check expiry
    if session.expires_at < datetime.utcnow():
        db.delete(session)
        db.commit()
        raise HTTPException(401, "Session expired — please log in again")

    # Step 4: Get the user
    user = db.query(User).filter(User.id == session.user_id).first()
    if not user:
        raise HTTPException(401, "User not found")

    # Step 5: Check if user is active
    if not user.active:
        raise HTTPException(403, "Account deactivated")

    return user
