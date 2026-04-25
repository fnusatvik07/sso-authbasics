# OAuth 2.0 vs OIDC (OpenID Connect)

## The Core Difference

```
OAuth 2.0:  "Can this app access my Google Calendar?"   → AUTHORIZATION
OIDC:       "Prove to this app that I am satvik@gmail"   → AUTHENTICATION
```

They often get mixed up because OIDC is built ON TOP of OAuth 2.0. OIDC uses the same flow but adds identity.

## OAuth 2.0 — Authorization

OAuth answers: "Does this app have PERMISSION to do X?"

Example: Your app wants to read a user's Google Calendar.
- The user must consent: "Yes, SSO Demo can see my calendar"
- Google gives your app an ACCESS TOKEN
- Your app uses that token to call the Calendar API

OAuth does NOT tell your app WHO the user is. It only gives permission to access resources.

## OIDC — Authentication

OIDC answers: "WHO is this person?"

Example: User clicks "Sign in with Google."
- Google authenticates the user
- Google gives your app an ID TOKEN (a signed proof of identity)
- Your app reads the ID token: email, name, Google user ID
- Your app now knows who the user is

## The Tokens

| Token | Purpose | Who creates it | Lifetime | Example use |
|-------|---------|---------------|----------|-------------|
| ID Token | Proves identity (who you are) | Google (IdP) | Short (minutes) | Read once at login to get email/name |
| Access Token | Grants API access (what you can do) | Google (authorization server) | ~1 hour | Call Google Calendar API |
| Refresh Token | Gets new access tokens silently | Google (authorization server) | Months/years | Auto-renew expired access tokens |

## ID Token (JWT) Decoded

An ID token looks like: `eyJhbGci...` (Base64-encoded JSON)

Decoded:
```json
{
  "sub": "1234567890",              ← stable Google user ID (never changes)
  "email": "satvik@gmail.com",      ← user's email
  "name": "Satvik",                 ← display name
  "iss": "accounts.google.com",     ← who issued this (Google)
  "aud": "941569587783-1fff...",    ← who this is for (YOUR app's client_id)
  "exp": 1714000000                 ← expiry timestamp
}
```

Your app validates:
- `iss` → is this really from Google?
- `aud` → is this meant for MY app?
- `exp` → is this still valid?
- Signature → has anyone tampered with it?

## Scopes — What You're Asking For

Scopes tell Google what you want access to.

| Scope | What it gives |
|-------|--------------|
| `openid` | Enables OIDC mode — gives you an ID token |
| `email` | User's email address |
| `profile` | User's name and profile picture |
| `https://www.googleapis.com/auth/calendar.readonly` | Read-only access to Google Calendar |

For login: `scope="openid email profile"`
For calendar: `scope="https://www.googleapis.com/auth/calendar.readonly"`

## In Our Project

### Login (OIDC)
```
Scope:     openid email profile
Token:     ID token → read email, name, sub
Purpose:   Know WHO the user is
Result:    Create user in DB + session cookie
```

### Calendar (OAuth)
```
Scope:     calendar.readonly
Tokens:    access_token + refresh_token
Purpose:   Access the user's calendar data
Result:    Store tokens in DB, call Calendar API
```

### Key Insight

Login and Calendar use the SAME OAuth flow (redirect → consent → code → token exchange).
The difference is the SCOPE and which TOKEN you care about.

```
Same flow, different scope → different result
openid email profile    → "I know who you are"
calendar.readonly       → "I can read your calendar"
```
