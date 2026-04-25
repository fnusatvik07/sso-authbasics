# Dynamic SSO Configuration

## The difference from what we built

In our multi-provider branch, the OAuth config is in `.env`:

```
GOOGLE_CLIENT_ID=123-abc.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xyz123
```

This works for ONE app with fixed providers. But in enterprise B2B SaaS:

- Acme uses Okta
- TechCorp uses Azure AD
- StartupXYZ uses Google Workspace
- Each has their OWN client_id and client_secret

You can't put all of them in `.env`. The config lives in the database, per org.

## The SSOConnection model

```python
class SSOConnection(Base):
    __tablename__ = "sso_connections"

    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("orgs.id"))

    provider = Column(String)          # "oidc" or "saml"

    # OIDC fields
    issuer_url = Column(String)        # https://acme.okta.com
    client_id = Column(String)         # app ID at the IdP
    client_secret = Column(String)     # app secret at the IdP

    # SAML fields
    metadata_url = Column(String)      # IdP's SAML metadata
    entity_id = Column(String)         # how IdP identifies your app
    acs_url = Column(String)           # assertion consumer service URL
    certificate = Column(Text)         # IdP's X.509 cert for signature verification

    enabled = Column(Boolean)          # toggle without deleting
```

Each org has ONE row in this table with their IdP's configuration.

## The login flow — dynamic routing

```
1. User visits your login page
2. User enters their email: priya@acme.com
3. App extracts domain: acme.com
4. App finds org: SELECT * FROM orgs WHERE domain = 'acme.com'
5. App finds SSO config: SELECT * FROM sso_connections WHERE org_id = 1
6. SSO config says: provider=oidc, issuer_url=https://acme.okta.com
7. App fetches OIDC discovery from https://acme.okta.com/.well-known/openid-configuration
8. App gets the authorization_endpoint from discovery
9. App redirects browser to Okta's login page
10. After login, Okta redirects back to /sso/callback
11. App exchanges code using the org's client_id + client_secret from the DB
12. Session created (same as always)
```

The key difference: **client_id and client_secret come from the database, not .env.**

```python
# Phase 2 (hardcoded):
oauth = OAuth2Session(
    client_id=GOOGLE_CLIENT_ID,           # from .env
    client_secret=GOOGLE_CLIENT_SECRET,   # from .env
)

# Dynamic SSO:
sso_conn = db.query(SSOConnection).filter(SSOConnection.org_id == org.id).first()
oauth = OAuth2Session(
    client_id=sso_conn.client_id,         # from database
    client_secret=sso_conn.client_secret, # from database
)
```

## State parameter carries routing info

In Phase 2, state was just for CSRF. In dynamic SSO, state also tells the callback which org's config to use:

```python
# Login
state = secrets.token_hex(16)
pending_sso_states[state] = sso_conn.id    # remember which SSO config

# Callback
sso_conn_id = pending_sso_states[state]    # look up which org
sso_conn = db.query(SSOConnection).filter(SSOConnection.id == sso_conn_id).first()
# now use sso_conn.client_id, sso_conn.client_secret, etc.
```

## Admin configuration UI

The admin page lets each org's admin configure their own SSO:

```
SSO Configuration for Acme Inc
─────────────────────────────

Provider:     [OIDC ▼]  /  [SAML]

OIDC Settings:
  Issuer URL:      [https://acme.okta.com      ]
  Client ID:       [0oa1234567890abcdef         ]
  Client Secret:   [••••••••••••••••••••••••••••]

  [Save]  [Test Connection]  [Disable SSO]
```

The client_secret is stored in the database but NEVER returned in API responses:

```python
@router.get("/sso/config")
def get_sso_config(user = Depends(require_role("admin"))):
    sso = db.query(SSOConnection).filter(SSOConnection.org_id == user.org_id).first()
    return {
        "provider": sso.provider,
        "issuer_url": sso.issuer_url,
        "client_id": sso.client_id,
        # client_secret intentionally NOT returned
    }
```

## Kill switch

The `enabled` field lets admins disable SSO without deleting the configuration:

```python
if not sso_conn.enabled:
    raise HTTPException(400, "SSO is disabled for this organization")
```

Useful when something breaks and you need to quickly turn off SSO while keeping the config intact.

## The teaching point

```
Phase 2:  One provider, config in .env, same for all users
Phase 3:  Multiple providers, config in .env, user picks which one
Dynamic:  Each ORG has its own provider, config in DATABASE, routed by email domain

The session layer is identical in all three.
```
