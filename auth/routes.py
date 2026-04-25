"""
Multi-provider OAuth Login — Phase 3.

Three providers, ONE session mechanism. The login endpoints are different
but they all end at the same place: _create_session().

  GET /auth/google/login      → redirects to Google
  GET /auth/google/callback   → Google sends user back here

  GET /auth/microsoft/login   → redirects to Microsoft
  GET /auth/microsoft/callback → Microsoft sends user back here

  GET /auth/github/login      → redirects to GitHub
  GET /auth/github/callback   → GitHub sends user back here

  POST /auth/logout           → same as always
  GET  /auth/me               → same as always

The session/cookie mechanism is IDENTICAL across all providers.
"""

import secrets
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session as DBSession
from authlib.integrations.requests_client import OAuth2Session
import requests as http_requests

from database import get_db
from models import User, SessionRecord
from config import (
    GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_AUTH_URL, GOOGLE_TOKEN_URL, GOOGLE_USERINFO_URL, GOOGLE_SCOPE,
    MICROSOFT_CLIENT_ID, MICROSOFT_CLIENT_SECRET, MICROSOFT_AUTH_URL, MICROSOFT_TOKEN_URL, MICROSOFT_USERINFO_URL, MICROSOFT_SCOPE,
    GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, GITHUB_AUTH_URL, GITHUB_TOKEN_URL, GITHUB_USERINFO_URL, GITHUB_SCOPE,
    REDIRECT_BASE, FRONTEND_URL,
)

router = APIRouter(prefix="/auth", tags=["auth"])

SESSION_DURATION_HOURS = 24

# CSRF state store (production: use Redis)
pending_states: dict[str, str] = {}  # state -> provider name


# ── Helper: create session + set cookie ──────────────
# IDENTICAL across all providers. This never changes.

def _create_session(user: User, response: Response, db: DBSession):
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


def _find_or_create_user(email: str, name: str, picture: str, db: DBSession) -> User:
    """Find existing user or create new one. Same for all providers."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email, name=name, picture=picture)
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        user.name = name
        if picture:
            user.picture = picture
        db.commit()
    return user


# ══════════════════════════════════════════════════════
#  GOOGLE
# ══════════════════════════════════════════════════════

@router.get("/google/login")
def google_login():
    state = secrets.token_hex(16)
    pending_states[state] = "google"

    oauth = OAuth2Session(
        client_id=GOOGLE_CLIENT_ID,
        redirect_uri=f"{REDIRECT_BASE}/auth/google/callback",
        scope=GOOGLE_SCOPE,
    )
    url, _ = oauth.create_authorization_url(GOOGLE_AUTH_URL, state=state)
    return RedirectResponse(url=url)


@router.get("/google/callback")
def google_callback(code: str, state: str, db: DBSession = Depends(get_db)):
    if state not in pending_states or pending_states[state] != "google":
        raise HTTPException(400, "Invalid state — possible CSRF attack")
    del pending_states[state]

    oauth = OAuth2Session(
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        redirect_uri=f"{REDIRECT_BASE}/auth/google/callback",
    )
    oauth.fetch_token(GOOGLE_TOKEN_URL, code=code)

    user_info = oauth.get(GOOGLE_USERINFO_URL).json()
    user = _find_or_create_user(
        email=user_info["email"],
        name=user_info.get("name", user_info["email"]),
        picture=user_info.get("picture"),
        db=db,
    )

    response = RedirectResponse(url=FRONTEND_URL, status_code=302)
    _create_session(user, response, db)
    return response


# ══════════════════════════════════════════════════════
#  MICROSOFT (Entra ID / Azure AD)
# ══════════════════════════════════════════════════════

@router.get("/microsoft/login")
def microsoft_login():
    state = secrets.token_hex(16)
    pending_states[state] = "microsoft"

    oauth = OAuth2Session(
        client_id=MICROSOFT_CLIENT_ID,
        redirect_uri=f"{REDIRECT_BASE}/auth/microsoft/callback",
        scope=MICROSOFT_SCOPE,
    )
    url, _ = oauth.create_authorization_url(MICROSOFT_AUTH_URL, state=state)
    return RedirectResponse(url=url)


@router.get("/microsoft/callback")
def microsoft_callback(code: str, state: str, db: DBSession = Depends(get_db)):
    if state not in pending_states or pending_states[state] != "microsoft":
        raise HTTPException(400, "Invalid state — possible CSRF attack")
    del pending_states[state]

    oauth = OAuth2Session(
        client_id=MICROSOFT_CLIENT_ID,
        client_secret=MICROSOFT_CLIENT_SECRET,
        redirect_uri=f"{REDIRECT_BASE}/auth/microsoft/callback",
    )
    oauth.fetch_token(MICROSOFT_TOKEN_URL, code=code)

    # Microsoft Graph returns different field names than Google
    user_info = oauth.get(MICROSOFT_USERINFO_URL).json()
    user = _find_or_create_user(
        email=user_info.get("mail") or user_info.get("userPrincipalName", ""),
        name=user_info.get("displayName", user_info.get("mail", "")),
        picture=None,  # Microsoft Graph photo requires a separate API call
        db=db,
    )

    response = RedirectResponse(url=FRONTEND_URL, status_code=302)
    _create_session(user, response, db)
    return response


# ══════════════════════════════════════════════════════
#  GITHUB
# ══════════════════════════════════════════════════════

@router.get("/github/login")
def github_login():
    state = secrets.token_hex(16)
    pending_states[state] = "github"

    oauth = OAuth2Session(
        client_id=GITHUB_CLIENT_ID,
        redirect_uri=f"{REDIRECT_BASE}/auth/github/callback",
        scope=GITHUB_SCOPE,
    )
    url, _ = oauth.create_authorization_url(GITHUB_AUTH_URL, state=state)
    return RedirectResponse(url=url)


@router.get("/github/callback")
def github_callback(code: str, state: str, db: DBSession = Depends(get_db)):
    if state not in pending_states or pending_states[state] != "github":
        raise HTTPException(400, "Invalid state — possible CSRF attack")
    del pending_states[state]

    # GitHub token endpoint needs Accept header for JSON response
    token_resp = http_requests.post(GITHUB_TOKEN_URL, data={
        "client_id": GITHUB_CLIENT_ID,
        "client_secret": GITHUB_CLIENT_SECRET,
        "code": code,
        "redirect_uri": f"{REDIRECT_BASE}/auth/github/callback",
    }, headers={"Accept": "application/json"})
    access_token = token_resp.json().get("access_token")

    # Get user info
    headers = {"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
    user_info = http_requests.get(GITHUB_USERINFO_URL, headers=headers).json()

    # GitHub may not return email in profile — fetch from emails endpoint
    email = user_info.get("email")
    if not email:
        emails = http_requests.get("https://api.github.com/user/emails", headers=headers).json()
        primary = next((e for e in emails if e.get("primary")), None)
        email = primary["email"] if primary else ""

    user = _find_or_create_user(
        email=email,
        name=user_info.get("name") or user_info.get("login", email),
        picture=user_info.get("avatar_url"),
        db=db,
    )

    response = RedirectResponse(url=FRONTEND_URL, status_code=302)
    _create_session(user, response, db)
    return response


# ══════════════════════════════════════════════════════
#  PROVIDERS LIST (for frontend to know what's available)
# ══════════════════════════════════════════════════════

@router.get("/providers")
def list_providers():
    """Returns which providers are configured (have client_id set)."""
    return {
        "google": bool(GOOGLE_CLIENT_ID),
        "microsoft": bool(MICROSOFT_CLIENT_ID),
        "github": bool(GITHUB_CLIENT_ID),
    }


# ══════════════════════════════════════════════════════
#  LOGOUT + ME (unchanged, works with ANY provider)
# ══════════════════════════════════════════════════════

@router.post("/logout")
def logout(request: Request, db: DBSession = Depends(get_db)):
    token = request.cookies.get("session_token")
    if token:
        session = db.query(SessionRecord).filter(
            SessionRecord.session_token == token
        ).first()
        if session:
            db.delete(session)
            db.commit()

    response = Response(content='{"detail":"Logged out"}', media_type="application/json")
    response.delete_cookie("session_token")
    return response


@router.get("/me")
def get_me(request: Request, db: DBSession = Depends(get_db)):
    token = request.cookies.get("session_token")
    if not token:
        raise HTTPException(401, "Not logged in")

    session = db.query(SessionRecord).filter(SessionRecord.session_token == token).first()
    if not session:
        raise HTTPException(401, "Invalid session")

    if session.expires_at < datetime.utcnow():
        db.delete(session)
        db.commit()
        raise HTTPException(401, "Session expired")

    user = db.query(User).filter(User.id == session.user_id).first()
    if not user or not user.active:
        raise HTTPException(401, "User not found or deactivated")

    return {"id": user.id, "email": user.email, "name": user.name, "picture": user.picture}
