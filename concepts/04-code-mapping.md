# Concept 4: Code Mapping — What Each File Does

## Flow → Code

```
User clicks "Login with Google"
        ↓
  GET /auth/google/login          →  auth/routes.py :: google_login()
        ↓
  Browser redirected to Google
        ↓
  User logs in at Google
        ↓
  Google redirects to:
  GET /auth/callback?code=...     →  auth/routes.py :: google_callback()
        ↓
  Server exchanges code for token  →  authlib OAuth2Session
        ↓
  Server reads user info           →  Google userinfo endpoint
        ↓
  Find or create User              →  models.py :: User table
        ↓
  Create SessionRecord             →  models.py :: SessionRecord table
        ↓
  Set cookie on response           →  response.set_cookie("session_token", ...)
        ↓
  Redirect to frontend             →  http://localhost:5173
```

## File Responsibilities

```
config.py          → Loads GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET from .env
database.py        → SQLAlchemy engine + session factory + Base class
models.py          → User and SessionRecord table definitions
auth/__init__.py   → Makes auth/ a Python package
auth/routes.py     → Login, callback, logout, /me endpoints
app.py             → Wires everything together, creates tables on startup
```

## The 3 Most Important Lines

```python
# 1. Exchange code for tokens (server-to-server, secret stays on server)
oauth.fetch_token(GOOGLE_TOKEN_URL, code=code)

# 2. Read who the user is
user_info = oauth.get(GOOGLE_USERINFO_URL).json()

# 3. Create session cookie (browser remembers login)
response.set_cookie(key="session_token", value=token, httponly=True)
```

## CORS Note

For the frontend (localhost:5173) to send cookies to the backend
(localhost:8000), we need:
- Backend: `allow_credentials=True` in CORS middleware
- Frontend: `credentials: "include"` in fetch() calls
