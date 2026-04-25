# Multi-Tenant Architecture

## The problem

You're building a B2B SaaS app. Multiple companies use it. Each company (tenant) needs:
- Their own users
- Their own SSO configuration (Okta, Azure AD, etc.)
- Their own audit logs
- Isolation — Acme can't see TechCorp's data

## How it works

Every user belongs to an **Org** (organization). The org is determined by their email domain.

```
priya@acme.com     → Org: Acme (domain: acme.com)
rahul@acme.com     → Org: Acme (domain: acme.com)
neha@techcorp.io   → Org: TechCorp (domain: techcorp.io)
```

### The Org model

```python
class Org(Base):
    __tablename__ = "orgs"

    id = Column(Integer, primary_key=True)
    name = Column(String)                    # "Acme Inc"
    domain = Column(String, unique=True)     # "acme.com"
    scim_token = Column(String)              # for SCIM provisioning
    domain_verified = Column(Boolean)        # did they prove they own acme.com?
```

### Domain-based routing

When a user logs in via SSO, the app extracts the domain from their email and finds the matching org:

```python
email = "priya@acme.com"
domain = email.split("@")[1]           # "acme.com"
org = db.query(Org).filter(Org.domain == domain).first()
# org.id = 1 (Acme)
```

This is how each company gets routed to their own SSO configuration without any manual setup.

### Tenant isolation in the database

Every query filters by `org_id`:

```python
# Admin viewing members — only sees their own org
members = db.query(User).filter(User.org_id == user.org_id).all()

# Admin viewing audit logs — only sees their own org
logs = db.query(AuditLog).filter(AuditLog.org_id == user.org_id).all()

# SSO config — each org has its own
sso = db.query(SSOConnection).filter(SSOConnection.org_id == org.id).first()
```

Acme's admin can never see TechCorp's users, logs, or SSO config.

### Database structure

```
orgs table:
┌────┬───────────┬─────────────┬───────────────┐
│ id │ name      │ domain      │ domain_verified│
├────┼───────────┼─────────────┼───────────────┤
│ 1  │ Acme Inc  │ acme.com    │ true          │
│ 2  │ TechCorp  │ techcorp.io │ true          │
└────┴───────────┴─────────────┴───────────────┘

users table:
┌────┬──────────────────┬────────┬────────┐
│ id │ email            │ org_id │ role   │
├────┼──────────────────┼────────┼────────┤
│ 1  │ priya@acme.com   │ 1      │ admin  │
│ 2  │ rahul@acme.com   │ 1      │ user   │
│ 3  │ neha@techcorp.io │ 2      │ admin  │
└────┴──────────────────┴────────┴────────┘

sso_connections table:
┌────┬────────┬──────────┬─────────────────────────────┐
│ id │ org_id │ provider │ issuer_url                  │
├────┼────────┼──────────┼─────────────────────────────┤
│ 1  │ 1      │ oidc     │ https://acme.okta.com       │
│ 2  │ 2      │ saml     │ (uses metadata_url instead) │
└────┴────────┴──────────┴─────────────────────────────┘

Each org has its own IdP. Acme uses Okta (OIDC). TechCorp uses Azure AD (SAML).
```

## Domain verification

Before an org can claim `acme.com`, they must prove they own it. Otherwise anyone could register as `google.com` and intercept Google employees' logins.

```
1. Admin clicks "Verify domain"
2. Server generates a random token: "sso-verify=abc123xyz"
3. Admin adds a DNS TXT record to acme.com with that value
4. Admin clicks "Check verification"
5. Server does DNS lookup: dig TXT acme.com
6. If the TXT record matches → domain_verified = True
```

This is the same pattern used by Google Workspace, Microsoft 365, and every email provider.

## JIT (Just-In-Time) Provisioning

Users don't need to be pre-created. When someone logs in via SSO for the first time, the app automatically:
1. Creates the user
2. Assigns them to the correct org (by email domain)
3. Sets role to "user" (unless they're the first person → "admin")

```python
user = db.query(User).filter(User.email == email).first()
if not user:
    org = db.query(Org).filter(Org.domain == email_domain).first()
    user = User(email=email, name=name, org_id=org.id, role="user")
    db.add(user)
```

No admin needs to manually add users. They just appear when they first log in through the company's IdP.
