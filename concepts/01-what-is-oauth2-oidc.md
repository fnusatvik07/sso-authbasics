# Concept 1: What is OAuth2 and OIDC?

## The Problem

Your app needs to know WHO the user is. You could build your own
username/password system, but that means:

- You store passwords (security risk)
- Users create yet another account (bad UX)
- You handle password resets, 2FA, etc.

**Better idea:** Let Google handle login. Users already have Google accounts.

---

## OAuth2 = Authorization (what can you access?)

OAuth2 is a protocol that lets your app **request access** to a user's
data on another service (like Google).

Example: "Can my app read your Google Calendar?"

OAuth2 answers: **what are you allowed to do?**

## OIDC = Authentication (who are you?)

OpenID Connect (OIDC) is a **layer on top of OAuth2** that adds identity.

It answers: **who is this person?** (email, name, profile picture)

```
OAuth2 alone:  "Here's a token to access the Calendar API"
OAuth2 + OIDC: "Here's a token AND this person is alice@gmail.com"
```

For login, we use **OIDC** (which includes OAuth2 under the hood).

---

## The 4 Players

```
+------------------+     +------------------+
|   User (You)     |     |   Google (IdP)   |
|   sitting at     |     |   Identity       |
|   browser        |     |   Provider       |
+--------+---------+     +--------+---------+
         |                         |
+--------+---------+     +--------+---------+
|   Browser        |     |   Your App       |
|   (User Agent)   |     |   (FastAPI)      |
+------------------+     +------------------+
```

- **User** — the human logging in
- **Browser** — sends requests, holds cookies
- **Google (IdP)** — knows the user's identity, handles the login form
- **Your App** — wants to know who the user is

---

## Key Terms

| Term | What it is |
|------|-----------|
| **Client ID** | Your app's public identifier at Google |
| **Client Secret** | Your app's private password at Google (never shown to browser) |
| **Redirect URI** | Where Google sends the user back after login |
| **Authorization Code** | A one-time code Google gives you (exchanged for tokens) |
| **Access Token** | A key to call Google APIs on behalf of the user |
| **ID Token** | A JWT containing user info (email, name, picture) |
| **State** | A random string for CSRF protection |
| **Scope** | What you're asking for: `openid email profile` |

---

## Next: [02-google-login-flow.md](./02-google-login-flow.md) — The step-by-step login flow
