# Where Secrets Live

Every piece of sensitive data has a specific place where it should live. Putting it in the wrong place is a security vulnerability.

## The map

```
┌─────────────────────────────────────────────────────────────────┐
│                    WHERE SECRETS LIVE                            │
├──────────────────────┬──────────────────────────────────────────┤
│ .env file            │ OPENAI_API_KEY                           │
│ (server only,        │ GOOGLE_CLIENT_SECRET                     │
│  never committed)    │ MICROSOFT_CLIENT_SECRET                  │
│                      │ GITHUB_CLIENT_SECRET                     │
│                      │ Database password (if not SQLite)        │
├──────────────────────┼──────────────────────────────────────────┤
│ Database             │ User data (email, name)                  │
│ (server only)        │ Session tokens                           │
│                      │ SSO connection secrets (per-org)         │
│                      │ SCIM tokens (per-org)                    │
│                      │ Audit logs                               │
├──────────────────────┼──────────────────────────────────────────┤
│ Server memory        │ pending_states (CSRF tokens)             │
│ (runtime only,       │ Access tokens from Google/Microsoft      │
│  lost on restart)    │ ID tokens (read once, discarded)         │
├──────────────────────┼──────────────────────────────────────────┤
│ Browser cookie       │ session_token (HttpOnly, not readable    │
│ (set by server)      │ by JavaScript)                           │
├──────────────────────┼──────────────────────────────────────────┤
│ Browser URL          │ Authorization code (one-time, 5 min)     │
│ (visible briefly)    │ State parameter (CSRF token)             │
│                      │ Redirect URI                             │
├──────────────────────┼──────────────────────────────────────────┤
│ Google/IdP servers   │ User's password                          │
│ (never touches       │ User's 2FA                               │
│  your app)           │ Refresh tokens (if using offline access) │
├──────────────────────┼──────────────────────────────────────────┤
│ NEVER anywhere       │ Passwords in your database               │
│                      │ client_secret in frontend code           │
│                      │ Tokens in URL query strings (in prod)    │
│                      │ API keys in git commits                  │
└──────────────────────┴──────────────────────────────────────────┘
```

## Common mistakes

| Mistake | Why it's bad | Where it should be |
|---------|-------------|-------------------|
| client_secret in frontend JS | Anyone can see it in browser DevTools | .env on server |
| API keys committed to git | Anyone with repo access has your keys | .env (in .gitignore) |
| Session token in URL | Browser history, server logs, referrer headers leak it | HttpOnly cookie |
| Access tokens sent to browser | Frontend can be XSS'd, tokens stolen | Server memory only |
| Passwords stored in your DB | If DB is breached, all accounts compromised | Don't store passwords — use OAuth/OIDC |
| SCIM token in API response | Anyone who calls the API sees the token | Show once during generation, never return again |
