# Concept 3: Sessions and Cookies

## The Problem: HTTP is Stateless

Every HTTP request is independent. The server doesn't remember you.

```
Request 1: GET /dashboard  → Server: "Who are you?"
Request 2: GET /dashboard  → Server: "Who are you?" (again!)
```

We need a way to say "I already logged in" on every request.

---

## Solution: Session Token + Cookie

After login, the server:
1. Creates a **session** (random token stored in database)
2. Sends the token to the browser as a **cookie**
3. Browser auto-attaches the cookie on every future request

```
Login:
  Server → creates session_token = "abc123" → stores in DB
  Server → Set-Cookie: session_token=abc123

Every request after:
  Browser → Cookie: session_token=abc123
  Server  → looks up "abc123" in DB → finds user_id=7 → "Welcome back, Alice!"
```

---

## Cookie Security Flags

When setting the cookie, we use these flags to prevent attacks:

| Flag | What it does | Protects against |
|------|-------------|-----------------|
| `HttpOnly` | JavaScript can't read the cookie | XSS (cross-site scripting) |
| `SameSite=Lax` | Cookie only sent on same-site requests | CSRF (cross-site request forgery) |
| `Secure` | Cookie only sent over HTTPS | Man-in-the-middle attacks |
| `max_age` | Cookie expires after N seconds | Stale sessions |

```python
response.set_cookie(
    key="session_token",
    value=token,
    httponly=True,      # JS can't access
    samesite="lax",     # CSRF protection
    max_age=86400,      # 24 hours
)
```

---

## Session Lifecycle

```
1. LOGIN
   User proves identity (via Google) →
   Server creates SessionRecord in DB →
   Server sets cookie on response

2. EVERY REQUEST
   Browser sends cookie automatically →
   Server reads cookie →
   Server looks up session in DB →
   Server checks: expired? user active? →
   If valid → return user object
   If invalid → return 401

3. LOGOUT
   Server deletes session from DB →
   Server clears cookie from response →
   Browser forgets the cookie
```

---

## Why NOT just use JWTs as sessions?

JWTs (JSON Web Tokens) are popular, but for sessions they have a problem:
**you can't revoke them.** If a user logs out or gets deactivated,
the JWT is still valid until it expires.

With database sessions:
- Logout → delete from DB → instant revocation
- Deactivate user → next request checks DB → blocked immediately
- Admin can see/kill active sessions

**Rule of thumb:** Use DB sessions for auth. Use JWTs for API tokens.

---

## In our code

```python
# Creating a session (after Google login)
session_token = secrets.token_hex(32)     # random 64-char string
session = SessionRecord(
    session_token=session_token,
    user_id=user.id,
    expires_at=datetime.utcnow() + timedelta(hours=24),
)
db.add(session)

# Checking a session (on every request)
def get_current_user(request):
    token = request.cookies.get("session_token")
    session = db.query(SessionRecord).filter_by(session_token=token).first()
    if not session or session.expires_at < now:
        raise 401
    return session.user
```
