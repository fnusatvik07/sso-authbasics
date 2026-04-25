# OIDC Discovery — How Your App Finds the Right Endpoints

## The problem

In our multi-provider setup, we hardcoded the URLs:

```python
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
```

But in enterprise SSO, each customer uses a different IdP (Okta, Azure AD, Ping Identity, etc.). You can't hardcode all of them. And you shouldn't guess the URLs — Google alone uses 3 different domains for auth, token, and userinfo.

## The solution: OIDC Discovery

Every OIDC-compliant provider publishes a JSON document at a well-known URL:

```
{issuer_url}/.well-known/openid-configuration
```

For example:

```
Google:     https://accounts.google.com/.well-known/openid-configuration
Okta:       https://acme.okta.com/.well-known/openid-configuration
Azure AD:   https://login.microsoftonline.com/{tenant}/v2.0/.well-known/openid-configuration
```

### What's in the discovery document

```json
{
  "issuer": "https://accounts.google.com",
  "authorization_endpoint": "https://accounts.google.com/o/oauth2/v2/auth",
  "token_endpoint": "https://oauth2.googleapis.com/token",
  "userinfo_endpoint": "https://openidconnect.googleapis.com/v1/userinfo",
  "jwks_uri": "https://www.googleapis.com/oauth2/v3/certs",
  "end_session_endpoint": "https://accounts.google.com/o/oauth2/revoke",
  "scopes_supported": ["openid", "email", "profile"],
  "response_types_supported": ["code", "token", "id_token"],
  ...
}
```

**One URL gives you everything.** The admin only needs to provide the `issuer_url`. Your app fetches the rest automatically.

### How it's used in code

```python
def fetch_oidc_config(issuer_url: str) -> dict:
    """Fetch OIDC discovery document from the issuer."""
    url = f"{issuer_url.rstrip('/')}/.well-known/openid-configuration"
    response = requests.get(url, timeout=10)
    return response.json()

# Usage
config = fetch_oidc_config("https://acme.okta.com")
auth_url = config["authorization_endpoint"]      # where to redirect
token_url = config["token_endpoint"]              # where to exchange code
userinfo_url = config["userinfo_endpoint"]        # where to get user info
```

### Why not just hardcode?

```
Google auth:     accounts.google.com/o/oauth2/v2/auth
Google token:    oauth2.googleapis.com/token         ← different domain!
Google userinfo: openidconnect.googleapis.com/v1/userinfo  ← yet another domain!
```

If you guessed `accounts.google.com/token`, it wouldn't work. Discovery eliminates guessing.

### Tenant-aware SSO flow with discovery

```
1. User enters email: priya@acme.com
2. App extracts domain: acme.com
3. App finds org by domain → org_id = 1
4. App finds SSO config for org → issuer_url = "https://acme.okta.com"
5. App fetches: https://acme.okta.com/.well-known/openid-configuration
6. App reads authorization_endpoint from the document
7. App redirects user to Okta's login page
8. After login, app reads token_endpoint from the document
9. App exchanges code for tokens at that URL
```

The admin only configured ONE value: `issuer_url`. Everything else was discovered automatically.

### Error handling

What if the discovery URL is unreachable or returns garbage?

```python
def fetch_oidc_config(issuer_url: str) -> dict:
    discovery_url = issuer_url.rstrip("/") + "/.well-known/openid-configuration"
    response = requests.get(discovery_url, timeout=10)
    response.raise_for_status()   # raises exception if 404, 500, etc.

    config = response.json()

    # Verify required fields are present
    required = ["authorization_endpoint", "token_endpoint"]
    for field in required:
        if field not in config:
            raise ValueError(f"OIDC discovery missing required field: {field}")

    return config
```

Common failures:
- Wrong issuer_url → 404
- Corporate firewall blocking outbound requests → timeout
- IdP is down → 500
- Non-OIDC provider (GitHub is NOT OIDC) → missing fields

### Try it yourself

Open these URLs in a browser to see real discovery documents:

```
Google:    https://accounts.google.com/.well-known/openid-configuration
Microsoft: https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration
Okta:      https://dev-12345.okta.com/.well-known/openid-configuration
```

Compare the endpoints — they're all different. Discovery is the only reliable way to get them.

### What about SAML?

SAML doesn't have a `.well-known` endpoint. Instead, IdPs publish a **metadata XML** file:

```
https://acme.okta.com/app/abc123/sso/saml/metadata
```

This XML contains similar info — the SSO URL, the certificate for signature verification, the entity ID. Same concept, different format.

### What about GitHub?

GitHub is OAuth2 only — it does NOT support OIDC. There is no `/.well-known/openid-configuration` for GitHub. That's why in our multi-provider code, GitHub's URLs are hardcoded. OIDC discovery only works with OIDC-compliant providers.
