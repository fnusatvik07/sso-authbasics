# SCIM 2.0 — Automated User Provisioning

## The problem

Without SCIM, when a company hires or fires someone:

```
Manual process:
  HR adds employee to Okta
  Admin manually creates account in App 1
  Admin manually creates account in App 2
  Admin manually creates account in App 3
  ...
  
  Employee leaves → HR deactivates in Okta
  Admin forgets to remove from App 2
  → Ex-employee still has access to App 2
```

SCIM automates this. When someone is added or removed in the IdP, ALL connected apps are updated automatically.

## How SCIM works

SCIM is a REST API that the IdP (Okta, Azure AD) calls on YOUR server. The IdP pushes changes to you — you don't pull from the IdP.

```
IdP (Okta)                          Your App (AgentFlow)
    |                                      |
    |  1. Admin adds user in Okta          |
    |                                      |
    |  POST /scim/v2/Users                 |
    |  {"userName":"priya@acme.com",       |
    |   "name":{"givenName":"Priya"}}      |
    |------------------------------------->|
    |                                      |  → Creates user in DB
    |  201 Created                         |
    |<-------------------------------------|
    |                                      |
    |  2. Admin deactivates user in Okta   |
    |                                      |
    |  PATCH /scim/v2/Users/42             |
    |  {"Operations":[{"op":"Replace",     |
    |   "path":"active","value":false}]}   |
    |------------------------------------->|
    |                                      |  → Sets user.active = False
    |  200 OK                              |
    |<-------------------------------------|
```

## SCIM endpoints

| Method | Endpoint | What it does |
|--------|----------|-------------|
| GET | /scim/v2/Users | List all users (paginated) |
| GET | /scim/v2/Users/{id} | Get a single user |
| POST | /scim/v2/Users | Create a new user |
| PUT | /scim/v2/Users/{id} | Replace a user completely |
| PATCH | /scim/v2/Users/{id} | Partial update (especially active=false) |
| DELETE | /scim/v2/Users/{id} | Soft delete (set active=false) |

## Authentication — Bearer token, not cookies

SCIM doesn't use session cookies. It's server-to-server (Okta → your app). Authentication is via a **Bearer token**:

```
Authorization: Bearer abc123xyz...
```

Each org has its own SCIM token stored in the database:

```python
class Org(Base):
    scim_token = Column(String, unique=True)
```

The admin generates this token in your app's settings page, then pastes it into Okta's SCIM configuration. Okta sends it on every request.

```python
def verify_scim_token(request):
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    org = db.query(Org).filter(Org.scim_token == token).first()
    if not org:
        raise 401
    return org
```

## SCIM JSON format

SCIM uses its own JSON format — different from normal REST APIs.

### Create user request (from IdP):

```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
  "userName": "priya@acme.com",
  "name": {
    "givenName": "Priya",
    "familyName": "Sharma"
  },
  "emails": [
    {
      "value": "priya@acme.com",
      "primary": true
    }
  ],
  "active": true,
  "externalId": "okta-user-id-12345"
}
```

### Your response:

```json
{
  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
  "id": "42",
  "userName": "priya@acme.com",
  "name": {
    "givenName": "Priya",
    "familyName": "Sharma"
  },
  "active": true,
  "meta": {
    "resourceType": "User",
    "created": "2026-04-25T10:00:00Z"
  }
}
```

## The critical operation: PATCH active=false

When an employee is deactivated in Okta:

```json
PATCH /scim/v2/Users/42

{
  "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
  "Operations": [
    {
      "op": "Replace",
      "path": "active",
      "value": false
    }
  ]
}
```

Your app sets `user.active = False`. Now even if they have a valid session cookie, `get_current_user()` rejects them:

```python
def get_current_user(request, db):
    ...
    user = db.query(User).filter(User.id == session.user_id).first()
    if not user.active:                    # SCIM set this to False
        raise HTTPException(403, "Account deactivated")
```

This is why the `active` field exists on the User model — it's for SCIM deactivation.

## externalId — linking IdP users to your users

```
Okta user ID:     "00u1234abc"
Your app user ID: 42
```

The `externalId` field maps between the two. When Okta sends a PATCH for user `00u1234abc`, you look up which of your users has that external ID:

```python
user = db.query(User).filter(User.external_id == "00u1234abc").first()
```

## The full lifecycle

```
1. Company signs up for your app
2. Admin configures SSO (OIDC or SAML)
3. Admin generates SCIM token in your app
4. Admin pastes SCIM token + SCIM endpoint URL into Okta
5. Okta pushes all existing users via POST /scim/v2/Users
6. Users can now log in via SSO (JIT provisioning also works as backup)
7. New hire → Okta creates user → POST to your app → user appears
8. Employee leaves → Okta deactivates → PATCH to your app → user blocked
9. No manual work. No forgotten accounts. No security gaps.
```
