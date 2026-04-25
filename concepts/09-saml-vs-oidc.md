# SAML 2.0 — The Enterprise Protocol

## Why SAML still exists

OIDC (what we've been using) is modern, JSON-based, and developer-friendly. SAML is from 2005, XML-based, and verbose. But large enterprises (banks, hospitals, government) still use it because:

1. Their IdP (Active Directory Federation Services, Oracle) was set up before OIDC existed
2. Migrating thousands of apps from SAML to OIDC is expensive
3. SAML works fine — it's just older

If you're building B2B SaaS, you MUST support SAML. Your biggest customers will require it.

## OIDC vs SAML — Side by Side

| | OIDC | SAML |
|---|---|---|
| Data format | JSON | XML |
| Token format | JWT (compact) | XML Assertion (verbose) |
| Transport | HTTP redirects + REST API calls | HTTP POST with signed XML |
| Discovery | `/.well-known/openid-configuration` | Metadata XML file |
| Code exchange | Yes (authorization code flow) | No (assertion sent directly) |
| User info | Separate API call to /userinfo | Embedded in the assertion |
| Signature | JWT signature (compact) | XML signature (X.509 certificate) |
| Complexity | Simpler | More complex |
| Modern apps | Standard choice | Legacy/enterprise |

## The SAML Flow

```
OIDC (what we built):
  Browser → Your App → Google (redirect) → callback with CODE → exchange for tokens → get user info

SAML:
  Browser → Your App → IdP (redirect) → IdP POSTs signed XML directly to your app → done
```

SAML is actually fewer steps — no code exchange needed. The IdP sends the user's identity directly in a signed XML document.

### Step by step

```
1. User clicks "Login with SSO"

2. Your app builds a SAML AuthnRequest (XML)
   and redirects browser to the IdP's SSO URL

3. User logs in at the IdP (same as OIDC)

4. IdP builds a SAML Assertion (signed XML containing user identity)
   and POSTs it to your Assertion Consumer Service (ACS) URL
   
   This is different from OIDC — the IdP sends a POST, not a redirect.
   The assertion is in the POST body, not the URL query string.

5. Your app:
   - Verifies the XML signature using the IdP's X.509 certificate
   - Reads email, name from the assertion
   - Creates session + sets cookie (SAME AS ALWAYS)
```

### Key SAML terms

| Term | What it means | OIDC equivalent |
|------|--------------|-----------------|
| **Service Provider (SP)** | Your app | Client (your app) |
| **Identity Provider (IdP)** | Okta, Azure AD | Google, Microsoft |
| **Assertion** | Signed XML with user identity | ID Token (JWT) |
| **ACS URL** | Where IdP POSTs the assertion | Callback/redirect URI |
| **Entity ID** | Unique identifier for your app | Client ID |
| **SSO URL** | IdP's login page | Authorization endpoint |
| **Certificate** | IdP's public key for signature verification | JWKS URI |
| **RelayState** | CSRF protection + routing info | State parameter |
| **NameID** | User's identifier (usually email) | sub claim in JWT |

### The SAML Assertion (simplified)

```xml
<saml:Assertion>
  <saml:Issuer>https://acme.okta.com</saml:Issuer>
  
  <ds:Signature>
    <!-- XML signature proving this came from Okta -->
    <!-- Verified using Okta's X.509 certificate -->
  </ds:Signature>
  
  <saml:Subject>
    <saml:NameID>priya@acme.com</saml:NameID>
  </saml:Subject>
  
  <saml:Conditions NotBefore="2026-04-25T10:00:00Z" NotOnOrAfter="2026-04-25T10:05:00Z">
    <saml:AudienceRestriction>
      <saml:Audience>https://agentflow.com</saml:Audience>
    </saml:AudienceRestriction>
  </saml:Conditions>
  
  <saml:AttributeStatement>
    <saml:Attribute Name="email">
      <saml:AttributeValue>priya@acme.com</saml:AttributeValue>
    </saml:Attribute>
    <saml:Attribute Name="firstName">
      <saml:AttributeValue>Priya</saml:AttributeValue>
    </saml:Attribute>
  </saml:AttributeStatement>
</saml:Assertion>
```

Compare this to the OIDC ID token — same information, just in XML instead of JSON.

### Signature verification

In OIDC, the JWT is signed and you verify it using the JWKS endpoint. In SAML, the XML is signed using an X.509 certificate. The IdP gives you their public certificate when you set up SAML.

```python
# Your app validates:
# 1. Is the signature valid? (using IdP's certificate)
# 2. Is the audience MY app? (prevents assertion reuse)
# 3. Is it expired? (NotOnOrAfter check)
# 4. Is the issuer the expected IdP?
```

### SP Metadata

Just like OIDC has a discovery document, SAML has SP (Service Provider) metadata — an XML file describing YOUR app to the IdP:

```xml
<EntityDescriptor entityID="https://agentflow.com">
  <SPSSODescriptor>
    <AssertionConsumerService 
      Location="http://localhost:8000/sso/saml/callback" 
      Binding="urn:oasis:names:tc:SAML:2.0:bindings:HTTP-POST" />
  </SPSSODescriptor>
</EntityDescriptor>
```

The admin pastes this URL into Okta/Azure AD, and the IdP knows where to send assertions.

## When to use which

```
Building a consumer app (social login)?     → OIDC only
Building B2B SaaS for startups?             → OIDC only  
Building B2B SaaS for enterprises?          → OIDC + SAML
Building for government/healthcare?         → Definitely SAML
```

## The session layer doesn't care

Whether the user logged in via OIDC or SAML, the session creation is identical:

```python
# After OIDC login
user = find_or_create_user(email, name)
_create_session(user, response, db)      # same function

# After SAML login  
user = find_or_create_user(email, name)
_create_session(user, response, db)      # exact same function
```

OIDC and SAML are just different ways to get the email. Everything after that is the same.
