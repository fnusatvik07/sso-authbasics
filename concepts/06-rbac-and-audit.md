# Role-Based Access Control (RBAC) and Audit Logging

## RBAC — Who can do what?

Authentication answers "who are you?" RBAC answers "what are you allowed to do?"

```
Authentication:  "This is Priya"
Authorization:   "Priya is an admin, she can manage users"

Authentication:  "This is Rahul"
Authorization:   "Rahul is a regular user, he can only chat"
```

### How it works in code

The User model has a `role` field:

```python
class User(Base):
    email = Column(String)
    name = Column(String)
    role = Column(String, default="user")   # "user" or "admin"
```

A dependency checks the role AFTER checking the session:

```python
def require_role(required_role: str):
    def inner(user = Depends(get_current_user)):   # first: is user logged in?
        if user.role != required_role:              # second: do they have the right role?
            raise HTTPException(403, "Access denied")
        return user
    return inner

# Usage
@app.get("/admin/settings")
def admin_settings(user = Depends(require_role("admin"))):
    # only admins reach this code
    ...
```

The chain is: **cookie → session → user → role check**

```
Request arrives
  → get_current_user()     checks cookie + session
    → require_role("admin") checks user.role == "admin"
      → route handler       only runs if both passed
```

### First user = admin

When the first person in an organization logs in, they automatically become admin:

```python
existing_members = db.query(User).filter(User.org_id == org_id).count()
if existing_members == 0:
    role = "admin"    # first person in the org
```

### Last admin protection

You can't remove the last admin from an org — otherwise nobody can manage it:

```python
admin_count = db.query(User).filter(User.org_id == org_id, User.role == "admin").count()
if admin_count <= 1 and user.role == "admin":
    raise "Can't remove the last admin"
```

## Audit Logging — Who did what, when?

Every important action gets logged in an `audit_logs` table. This is required for compliance (SOC 2, HIPAA, GDPR).

```
audit_logs table:
┌────┬─────────┬──────────────────┬──────────────────┬──────────────────┬────────────┐
│ id │ user_id │ email            │ action           │ detail           │ timestamp  │
├────┼─────────┼──────────────────┼──────────────────┼──────────────────┼────────────┤
│ 1  │ 2       │ priya@acme.com   │ login_google     │ Logged in via    │ 2026-04-25 │
│ 2  │ 2       │ priya@acme.com   │ role_changed     │ rahul→admin      │ 2026-04-25 │
│ 3  │ 3       │ rahul@acme.com   │ sso_configured   │ OIDC enabled     │ 2026-04-25 │
│ 4  │ 2       │ priya@acme.com   │ logout           │                  │ 2026-04-25 │
└────┴─────────┴──────────────────┴──────────────────┴──────────────────┴────────────┘
```

### Why store email separately?

If a user gets deleted, you still need to know WHO performed the action. The email field preserves this even if the user row is gone.

### Tenant isolation

Audit logs include `org_id`. An admin can only see their own org's logs:

```python
logs = db.query(AuditLog).filter(AuditLog.org_id == user.org_id).all()
```

Acme's admin can't see TechCorp's logs.

### What to log

| Action | When |
|--------|------|
| `login_google` | User logs in via Google |
| `login_sso` | User logs in via SSO |
| `logout` | User logs out |
| `role_changed` | Admin changes someone's role |
| `sso_configured` | Admin sets up SSO |
| `scim_user_created` | IdP creates a user via SCIM |
| `scim_user_deactivated` | IdP deactivates a user |
| `domain_verified` | Admin verifies domain ownership |

### The helper function

```python
def log_action(db, action: str, user=None, detail=None):
    log = AuditLog(
        user_id=user.id if user else None,
        email=user.email if user else None,
        action=action,
        detail=detail,
        org_id=user.org_id if user else None,
    )
    db.add(log)
    db.commit()
```

Called everywhere:
```python
log_action(db, "login_google", user=user, detail="Logged in via Google OIDC")
log_action(db, "role_changed", user=admin, detail=f"{target.email} role → admin")
```
