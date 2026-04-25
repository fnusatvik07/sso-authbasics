# Single Logout (SLO)

## The problem

Without SLO:

```
1. User logs out of your app
2. Your app deletes the session and clears the cookie
3. User visits your app again
4. Browser redirects to the IdP (Okta)
5. Okta still has an active session → silently re-authenticates
6. User is logged back in WITHOUT entering credentials

The user clicked "logout" but is immediately logged back in.
That's not what "logout" means.
```

## What SLO does

Single Logout terminates the session at BOTH your app AND the IdP.

```
Without SLO:
  Logout from your app    → Your session deleted
  IdP session             → Still active
  Visit your app again    → Silently re-authenticated (bad)

With SLO:
  Logout from your app    → Your session deleted
  Redirect to IdP logout  → IdP session also deleted
  Visit your app again    → Must enter credentials (correct)
```

## How it works (OIDC)

OIDC SLO uses the `end_session_endpoint` from the discovery document:

```python
# 1. Fetch the discovery document
config = fetch_oidc_config(issuer_url)
logout_url = config.get("end_session_endpoint")

# 2. Delete local session
db.delete(session)
db.commit()

# 3. Redirect to IdP's logout endpoint
redirect_url = f"{logout_url}?post_logout_redirect_uri=http://localhost:8000/ui/logged-out"
response = RedirectResponse(url=redirect_url)
response.delete_cookie("session_token")
return response
```

The flow:

```
1. User clicks "Logout" in your app
2. Your app deletes the session from DB
3. Your app clears the cookie
4. Your app redirects browser to the IdP's logout URL
5. IdP terminates its own session
6. IdP redirects browser to your post_logout_redirect_uri
7. User sees "You have been fully logged out"
```

### post_logout_redirect_uri

After the IdP finishes logging the user out, it needs to know where to send them. That's the `post_logout_redirect_uri` — usually a "You've been logged out" page on your app.

## SAML SLO

SAML SLO is more complex — it involves sending a signed `LogoutRequest` XML to the IdP's SingleLogoutService URL. The IdP responds with a `LogoutResponse`. In practice, many apps implement a simplified version that just redirects to the IdP's logout page.

## When SLO matters

```
Corporate environment:
  Shared computers in an office
  User logs out of your app to let someone else use the computer
  Without SLO → next person has access to the first person's account

Security-sensitive apps:
  Banking, healthcare, government
  "Logout means logout" — no silent re-authentication

Compliance:
  SOC 2, HIPAA require proper session termination
  Auditors check that logout actually ends all sessions
```

## When SLO doesn't matter

```
Personal devices:
  User logs out of their own laptop
  Re-authenticating silently is actually convenient

Consumer apps:
  Social login with Google
  Users expect to stay logged in across apps
```
