"""
Simple email login — Phase 1 (no Google yet).

We start with basic signup/login to teach HOW sessions work:
  - What happens in the database when you sign up
  - What a session token is and where it's stored
  - How a cookie carries the session on every request
  - What logout actually does (delete from DB + clear cookie)

Later (Phase 2) we'll replace this with Google OAuth.
Same session mechanics — just a different way to prove "I am alice@gmail.com".

Endpoints:
  POST /auth/signup    → Create a new user (email + name)
  POST /auth/login     → Login with email → create session → set cookie
  POST /auth/logout    → Delete session from DB → clear cookie
  GET  /auth/me        → Read cookie → lookup session → return user
"""

import secrets
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from database import get_db
from models import User, SessionRecord

router = APIRouter(prefix="/auth", tags=["auth"])

SESSION_DURATION_HOURS = 24


# ── Request schemas ──────────────────────────────────

class SignupRequest(BaseModel):
    email: str
    name: str


class LoginRequest(BaseModel):
    email: str


# ── Helper: create session + set cookie ──────────────

def _create_session(user: User, response: Response, db: DBSession):
    """
    This is the CORE of session-based auth. Two things happen:

    1. We generate a random token and store it in the 'sessions' table
       alongside the user_id and an expiry time.

    2. We set that token as a cookie on the HTTP response.
       The browser will automatically send this cookie on every
       future request — that's how the server knows "who" is asking.

    Think of it like a wristband at a concert:
      - The venue (server) gives you a wristband (cookie) at the door (login)
      - You show the wristband on every entry (every request)
      - The venue checks it against their list (session DB)
      - When you leave (logout), they cut the wristband and remove you from the list
    """
    token = secrets.token_hex(32)  # 64-char random string

    session = SessionRecord(
        session_token=token,
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=SESSION_DURATION_HOURS),
    )
    db.add(session)
    db.commit()

    # Set the cookie — browser stores this and sends it automatically
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,       # JavaScript can't read this cookie (XSS protection)
        samesite="lax",      # Cookie only sent on same-site requests (CSRF protection)
        max_age=SESSION_DURATION_HOURS * 3600,  # Browser deletes cookie after 24h
    )


# ==================== SIGNUP ====================

@router.post("/signup")
def signup(req: SignupRequest, db: DBSession = Depends(get_db)):
    """
    Create a new user in the database.

    What happens in the DB:
      INSERT INTO users (email, name) VALUES ('alice@test.com', 'Alice')

    No password for now — we're focusing on the session mechanism.
    In Phase 2, Google will verify identity instead of a password.
    """
    # Check if user already exists
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(400, "User already exists — try logging in")

    user = User(email=req.email, name=req.name)
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"detail": f"User created: {user.name} ({user.email})", "id": user.id}


# ==================== LOGIN ====================

@router.post("/login")
def login(req: LoginRequest, db: DBSession = Depends(get_db)):
    """
    Login with email → create session → set cookie.

    What happens:
      1. Find user by email in DB
      2. Generate random session token
      3. Store token in 'sessions' table (linked to user_id)
      4. Set token as HttpOnly cookie on the response

    After this, the browser has the cookie. Every future request
    automatically includes it. The server reads it in /auth/me
    and knows who's asking.

    No password check here — this is Phase 1 (teaching sessions).
    In Phase 2, Google OAuth will replace this identity verification.
    """
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(404, "User not found — sign up first")

    if not user.active:
        raise HTTPException(403, "Account deactivated")

    # Create session and set cookie
    response = Response(
        content=f'{{"detail":"Logged in as {user.name}","email":"{user.email}"}}',
        media_type="application/json",
    )
    _create_session(user, response, db)

    return response


# ==================== LOGOUT ====================

@router.post("/logout")
def logout(request: Request, db: DBSession = Depends(get_db)):
    """
    Logout = two things:
      1. Delete the session from the database (server forgets you)
      2. Clear the cookie from the browser (browser forgets the token)

    After this, the next request won't have a cookie,
    and even if someone stole the old cookie value,
    the server won't find it in the DB anymore.
    """
    token = request.cookies.get("session_token")
    if token:
        session = db.query(SessionRecord).filter(
            SessionRecord.session_token == token
        ).first()
        if session:
            db.delete(session)
            db.commit()

    response = Response(
        content='{"detail":"Logged out"}',
        media_type="application/json",
    )
    response.delete_cookie("session_token")
    return response


# ==================== WHO AM I? ====================

@router.get("/me")
def get_me(request: Request, db: DBSession = Depends(get_db)):
    """
    The frontend calls this on every page load to check: "Am I logged in?"

    What happens:
      1. Read the session_token cookie from the request
      2. Look it up in the 'sessions' table
      3. Check if it's expired
      4. Find the user linked to this session
      5. Return user info (or 401 if anything fails)

    This is the READ side of the session lifecycle.
    Login = WRITE (create session + set cookie)
    /me   = READ  (read cookie + lookup session)
    Logout = DELETE (remove session + clear cookie)
    """
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(401, "Not logged in — no session cookie found")

    session = db.query(SessionRecord).filter(
        SessionRecord.session_token == token
    ).first()
    if not session:
        raise HTTPException(401, "Invalid session — token not in database")

    if session.expires_at < datetime.utcnow():
        db.delete(session)
        db.commit()
        raise HTTPException(401, "Session expired — please log in again")

    user = db.query(User).filter(User.id == session.user_id).first()
    if not user or not user.active:
        raise HTTPException(401, "User not found or deactivated")

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
    }
