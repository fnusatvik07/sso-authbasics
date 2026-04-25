"""
Google OAuth2/OIDC login routes.

Two endpoints that implement the Authorization Code Flow:

  GET /auth/google/login
    → Redirects browser to Google's login page

  GET /auth/callback
    → Google redirects here with ?code=...&state=...
    → We exchange the code for tokens (server-to-server)
    → We read the user's email/name from the token
    → We create a session + set a cookie
    → We redirect to the frontend

  POST /auth/logout
    → Deletes session from DB, clears cookie

  GET /auth/me
    → Returns the current logged-in user (for the frontend)
"""

import secrets
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session as DBSession
from authlib.integrations.requests_client import OAuth2Session

from database import get_db
from models import User, SessionRecord
from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET

router = APIRouter(prefix="/auth", tags=["auth"])

SESSION_DURATION_HOURS = 24

# Google's standard OIDC endpoints (these never change)
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"

# Where Google sends the user back after login
REDIRECT_URI = "http://localhost:8000/auth/callback"

# Frontend URL to redirect to after login/logout
FRONTEND_URL = "http://localhost:5173"

# In-memory state store (production: use Redis or DB)
pending_states: dict[str, bool] = {}


def _create_session(user: User, response: Response, db: DBSession):
    """Create a session in DB and set the cookie on the response."""
    token = secrets.token_hex(32)
    session = SessionRecord(
        session_token=token,
        user_id=user.id,
        expires_at=datetime.now(timezone.utc) + timedelta(hours=SESSION_DURATION_HOURS),
    )
    db.add(session)
    db.commit()
    response.set_cookie(
        key="session_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=SESSION_DURATION_HOURS * 3600,
    )


# ==================== STEP 1: Redirect to Google ====================

@router.get("/google/login")
def google_login():
    """
    User clicks "Login with Google" → this endpoint redirects them to Google.

    We include:
      - client_id: so Google knows which app is asking
      - redirect_uri: where to send the user back
      - scope: what we want (email, name, profile)
      - state: random string for CSRF protection
    """
    state = secrets.token_hex(16)
    pending_states[state] = True

    oauth = OAuth2Session(
        client_id=GOOGLE_CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        scope="openid email profile",
    )
    url, _ = oauth.create_authorization_url(GOOGLE_AUTH_URL, state=state)

    return RedirectResponse(url=url)


# ==================== STEP 2: Google redirects back ====================

@router.get("/callback")
def google_callback(code: str, state: str, db: DBSession = Depends(get_db)):
    """
    Google redirects here with ?code=abc&state=xyz

    We:
      1. Verify the state (CSRF check)
      2. Exchange the code for tokens (server-to-server, secret never in browser)
      3. Read user info from Google
      4. Find or create user in our DB
      5. Create session + set cookie
      6. Redirect to frontend
    """

    # 1. CSRF check
    if state not in pending_states:
        raise HTTPException(400, "Invalid state — possible CSRF attack")
    del pending_states[state]

    # 2. Exchange code for tokens
    oauth = OAuth2Session(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
    )
    oauth.fetch_token(GOOGLE_TOKEN_URL, code=code)

    # 3. Get user info
    user_info = oauth.get(GOOGLE_USERINFO_URL).json()
    email = user_info["email"]
    name = user_info.get("name", email)
    picture = user_info.get("picture")

    # 4. Find or create user (Just-In-Time provisioning)
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, name=name, picture=picture)
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        # Update name/picture in case they changed
        user.name = name
        user.picture = picture
        db.commit()

    # 5. Create session + cookie
    response = RedirectResponse(url=FRONTEND_URL, status_code=302)
    _create_session(user, response, db)

    return response


# ==================== LOGOUT ====================

@router.post("/logout")
def logout(request: Request, db: DBSession = Depends(get_db)):
    """Delete session from DB, clear cookie."""
    token = request.cookies.get("session_token")
    if token:
        session = db.query(SessionRecord).filter(
            SessionRecord.session_token == token
        ).first()
        if session:
            db.delete(session)
            db.commit()

    response = Response(content='{"detail":"logged out"}', media_type="application/json")
    response.delete_cookie("session_token")
    return response


# ==================== WHO AM I? ====================

@router.get("/me")
def get_me(request: Request, db: DBSession = Depends(get_db)):
    """
    Frontend calls this to check if user is logged in.
    Returns user info if session is valid, 401 if not.
    """
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(401, "Not logged in")

    session = db.query(SessionRecord).filter(
        SessionRecord.session_token == token
    ).first()
    if not session:
        raise HTTPException(401, "Invalid session")

    if session.expires_at < datetime.utcnow():
        db.delete(session)
        db.commit()
        raise HTTPException(401, "Session expired")

    user = db.query(User).filter(User.id == session.user_id).first()
    if not user or not user.active:
        raise HTTPException(401, "User not found or deactivated")

    return {
        "id": user.id,
        "email": user.email,
        "name": user.name,
        "picture": user.picture,
    }
