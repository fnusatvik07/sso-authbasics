# Concept 2: Google Login Flow (Step by Step)

## The Authorization Code Flow

This is the **most secure** OAuth2 flow. Secrets never touch the browser.

```
Step 1: User clicks "Login with Google"
Step 2: Your app redirects browser to Google
Step 3: User logs in at Google (your app never sees the password)
Step 4: Google redirects back to your app with a CODE
Step 5: Your app exchanges the CODE for TOKENS (server-to-server)
Step 6: Your app reads user info from the token
Step 7: Your app creates a session and sets a cookie
```

---

## Detailed Flow

```
   Browser                    Your App (FastAPI)              Google
     |                              |                           |
     |  1. Click "Login"            |                           |
     |----------------------------->|                           |
     |                              |                           |
     |  2. Redirect to Google       |                           |
     |  (with client_id, scope,     |                           |
     |   redirect_uri, state)       |                           |
     |<-----------------------------|                           |
     |                              |                           |
     |  3. User sees Google login   |                           |
     |----------------------------------------------------->   |
     |                              |                           |
     |  4. User enters credentials  |                           |
     |  at Google (NOT your app)    |                           |
     |----------------------------------------------------->   |
     |                              |                           |
     |  5. Google redirects back    |                           |
     |  with ?code=abc&state=xyz    |                           |
     |----------------------------->|                           |
     |                              |                           |
     |                              |  6. Exchange code for     |
     |                              |  tokens (server-to-server)|
     |                              |-------------------------->|
     |                              |                           |
     |                              |  7. Google returns        |
     |                              |  access_token + id_token  |
     |                              |<--------------------------|
     |                              |                           |
     |                              |  8. Read user info        |
     |                              |  (email, name) from token |
     |                              |                           |
     |  9. Set session cookie       |                           |
     |  Redirect to dashboard       |                           |
     |<-----------------------------|                           |
```

---

## Why is this secure?

1. **Your app never sees the user's Google password**
   - Google handles the login form entirely

2. **The authorization code is useless alone**
   - It can only be exchanged with the client_secret
   - The client_secret lives on your server, never in the browser

3. **The state parameter prevents CSRF**
   - Your app generates a random `state` before redirecting
   - When Google redirects back, your app checks the `state` matches
   - An attacker can't forge this because they don't know the random value

4. **Tokens stay server-side**
   - The access_token and id_token are received server-to-server
   - The browser only gets a session cookie (not the Google tokens)

---

## What we'll build in code

| File | Purpose |
|------|---------|
| `app/config.py` | Load GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET from .env |
| `app/database.py` | SQLite database connection |
| `app/models.py` | User and Session tables |
| `app/auth/routes.py` | `/auth/google/login` and `/auth/callback` endpoints |
| `app/auth/dependencies.py` | `get_current_user` — the gatekeeper |

---

## Next: [03-sessions-and-cookies.md](./03-sessions-and-cookies.md) — How sessions work
