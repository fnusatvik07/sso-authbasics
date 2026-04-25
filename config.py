"""
Configuration — loads all OAuth provider credentials from .env

All URLs and secrets are in .env so you can switch providers
without touching code. Same authorization code flow for all three.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ── Google ────────────────────────────────────────
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_AUTH_URL = os.getenv("GOOGLE_AUTH_URL", "https://accounts.google.com/o/oauth2/v2/auth")
GOOGLE_TOKEN_URL = os.getenv("GOOGLE_TOKEN_URL", "https://oauth2.googleapis.com/token")
GOOGLE_USERINFO_URL = os.getenv("GOOGLE_USERINFO_URL", "https://openidconnect.googleapis.com/v1/userinfo")
GOOGLE_SCOPE = os.getenv("GOOGLE_SCOPE", "openid email profile")

# ── Microsoft (Entra ID / Azure AD) ───────────────
MICROSOFT_CLIENT_ID = os.getenv("MICROSOFT_CLIENT_ID")
MICROSOFT_CLIENT_SECRET = os.getenv("MICROSOFT_CLIENT_SECRET")
MICROSOFT_TENANT = os.getenv("MICROSOFT_TENANT", "common")  # "common" allows any Microsoft account
MICROSOFT_AUTH_URL = os.getenv("MICROSOFT_AUTH_URL", f"https://login.microsoftonline.com/{MICROSOFT_TENANT}/oauth2/v2.0/authorize")
MICROSOFT_TOKEN_URL = os.getenv("MICROSOFT_TOKEN_URL", f"https://login.microsoftonline.com/{MICROSOFT_TENANT}/oauth2/v2.0/token")
MICROSOFT_USERINFO_URL = os.getenv("MICROSOFT_USERINFO_URL", "https://graph.microsoft.com/v1.0/me")
MICROSOFT_SCOPE = os.getenv("MICROSOFT_SCOPE", "openid email profile User.Read")

# ── GitHub ────────────────────────────────────────
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
GITHUB_AUTH_URL = os.getenv("GITHUB_AUTH_URL", "https://github.com/login/oauth/authorize")
GITHUB_TOKEN_URL = os.getenv("GITHUB_TOKEN_URL", "https://github.com/login/oauth/access_token")
GITHUB_USERINFO_URL = os.getenv("GITHUB_USERINFO_URL", "https://api.github.com/user")
GITHUB_SCOPE = os.getenv("GITHUB_SCOPE", "read:user user:email")

# ── App settings ──────────────────────────────────
REDIRECT_BASE = os.getenv("REDIRECT_BASE", "http://localhost:8000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
