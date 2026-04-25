"""
Google OAuth Login — Phase 2.

What changed from Phase 1:
  - REMOVED: POST /auth/signup (no manual user creation)
  - REMOVED: POST /auth/login  (no trusting emails blindly)
  - ADDED:   GET  /auth/google/login   → redirects to Google's login page
  - ADDED:   GET  /auth/callback       → Google sends user back here with a code

What DIDN'T change:
  - _create_session()  → still the same token + cookie logic
  - POST /auth/logout  → still deletes session + clears cookie
  - GET  /auth/me      → still reads cookie + looks up session

The session/cookie mechanism is IDENTICAL to Phase 1.
The only difference is WHO verifies the user's identity:
  Phase 1: we trusted whatever email the user typed
  Phase 2: Google confirms "this person is really priya@gmail.com"
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

# Google's OIDC endpoints (these are standard, never change)
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"

# Where Google sends the user back after they log in
REDIRECT_URI = "http://localhost:8000/auth/callback"

# Where to send the user after login/logout completes
FRONTEND_URL = "http://localhost:5173"

# Temporary store for CSRF state values (production: use Redis)
pending_states: dict[str, bool] = {}


# ── Helper: create session + set cookie ──────────────
# THIS IS IDENTICAL TO PHASE 1 — not a single line changed

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


# ==================== GOOGLE LOGIN (replaces /signup + /login) ====================

@router.get("/google/login")
def google_login():
    """
    Step 1 of Google login: redirect the user to Google's login page.

    When the user clicks "Login with Google" on the frontend,
    the frontend redirects to this endpoint. We then redirect
    the browser to Google with:
      - client_id: so Google knows which app is asking
      - redirect_uri: where to send the user back after login
      - scope: what info we want (email, name, profile picture)
      - state: random string to prevent CSRF attacks
    """
    # Generate a random state for CSRF protection
    state = secrets.token_hex(16)
    pending_states[state] = True

    # Build the Google authorization URL
    oauth = OAuth2Session(
        client_id=GOOGLE_CLIENT_ID,
        redirect_uri=REDIRECT_URI,
        scope="openid email profile",
    )
    url, _ = oauth.create_authorization_url(GOOGLE_AUTH_URL, state=state)

    # Redirect the user's browser to Google
    return RedirectResponse(url=url)


@router.get("/callback")
def google_callback(code: str, state: str, db: DBSession = Depends(get_db)):
    """
    Step 2 of Google login: Google redirects back here.

    After the user logs in at Google, Google redirects to:
      http://localhost:8000/auth/callback?code=abc123&state=xyz789

    We then:
      1. Verify the state matches (CSRF protection)
      2. Exchange the code for tokens (server-to-server, secret stays on server)
      3. Use the token to ask Google "who is this person?"
      4. Find or create the user in our database
      5. Create session + set cookie (SAME as Phase 1!)
      6. Redirect to the frontend
    """

    # 1. CSRF check — does the state match what we sent?
    if state not in pending_states:
        raise HTTPException(400, "Invalid state parameter — possible CSRF attack")
    del pending_states[state]  # one-time use

    # 2. Exchange the authorization code for tokens
    #    This is a SERVER-TO-SERVER call. The client_secret never touches the browser.
    oauth = OAuth2Session(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
    )
    oauth.fetch_token(GOOGLE_TOKEN_URL, code=code)

    # 3. Ask Google: "Who is this person?"
    user_info = oauth.get(GOOGLE_USERINFO_URL).json()
    email = user_info["email"]
    name = user_info.get("name", email)
    picture = user_info.get("picture")

    # 4. Find or create user in our DB (Just-In-Time provisioning)
    #    First login? We create the user automatically.
    #    Returning user? We update their name/picture in case it changed.
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, name=name, picture=picture)
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.name = name
        user.picture = picture
        db.commit()

    # 5. Create session + set cookie
    #    THIS IS THE SAME _create_session() FROM PHASE 1
    #    Same token generation, same DB insert, same cookie flags
    response = RedirectResponse(url=FRONTEND_URL, status_code=302)
    _create_session(user, response, db)

    return response


# ==================== LOGOUT (UNCHANGED FROM PHASE 1) ====================

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


# ==================== WHO AM I? (UNCHANGED FROM PHASE 1) ====================

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
