# OAuth Provider Setup Guide

How to get credentials for each provider. All three use the same flow — only the registration portal differs.

## Google

**Portal:** https://console.cloud.google.com

**Steps:**
1. Go to **APIs & Services > OAuth consent screen**
2. Click **Branding** tab → set app name, support email
3. Click **Audience** tab → select External, add test users
4. Click **Data Access** tab → Add scopes: `openid`, `userinfo.email`, `userinfo.profile`
5. Go to **APIs & Services > Credentials**
6. Click **+ Create Credentials > OAuth client ID**
7. Application type: **Web application**
8. Authorized redirect URI: `http://localhost:8000/auth/google/callback`
9. Copy Client ID and Client Secret

**Add to .env:**
```
GOOGLE_CLIENT_ID=352640895776-xxxx.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxx
```

**Scopes used:** `openid email profile`
**Userinfo endpoint:** `https://openidconnect.googleapis.com/v1/userinfo`
**Returns:** `email`, `name`, `picture`, `email_verified`

## Microsoft (Entra ID / Azure AD)

**Portal:** https://portal.azure.com

**Steps:**
1. Go to **Microsoft Entra ID > App registrations** (or search "App registrations" in the top search bar)
2. Click **+ New registration**
3. Name: `AgentFlow`
4. Supported account types: **Accounts in any organizational directory and personal Microsoft accounts**
5. Redirect URI: select **Web**, enter `http://localhost:8000/auth/microsoft/callback`
6. Click **Register**
7. On the app overview page, copy the **Application (client) ID**
8. Go to **Certificates & secrets > + New client secret**
9. Description: `AgentFlow dev`, Expires: choose any
10. Copy the **Value** (not the Secret ID) — you can only see it once

**Add to .env:**
```
MICROSOFT_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
MICROSOFT_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
MICROSOFT_TENANT=common
```

**Tenant options:**
| Value | Who can log in |
|-------|---------------|
| `common` | Any Microsoft account (personal + work) |
| `organizations` | Only work/school accounts |
| `consumers` | Only personal Microsoft accounts (outlook.com, hotmail) |
| `your-tenant-id` | Only accounts in your specific organization |

**Scopes used:** `openid email profile User.Read`
**Userinfo endpoint:** `https://graph.microsoft.com/v1.0/me`
**Returns:** `mail` or `userPrincipalName`, `displayName`

## GitHub

**Portal:** https://github.com/settings/developers

**Steps:**
1. Go to **Settings > Developer settings > OAuth Apps**
2. Click **New OAuth App**
3. Application name: `AgentFlow`
4. Homepage URL: `http://localhost:5173`
5. Authorization callback URL: `http://localhost:8000/auth/github/callback`
6. Click **Register application**
7. Copy the **Client ID**
8. Click **Generate a new client secret**
9. Copy the secret — you can only see it once

**Add to .env:**
```
GITHUB_CLIENT_ID=Ov23lixxxxxxxxxxxxxxxxxx
GITHUB_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Scopes used:** `read:user user:email`
**Userinfo endpoint:** `https://api.github.com/user`
**Returns:** `login`, `name`, `email`, `avatar_url`

**Note:** GitHub may not return email in the user profile if the user has set it to private. The code handles this by calling `https://api.github.com/user/emails` as a fallback.

## Quick Reference

| | Google | Microsoft | GitHub |
|---|---|---|---|
| Registration portal | console.cloud.google.com | portal.azure.com | github.com/settings/developers |
| Redirect URI | /auth/google/callback | /auth/microsoft/callback | /auth/github/callback |
| .env: CLIENT_ID | GOOGLE_CLIENT_ID | MICROSOFT_CLIENT_ID | GITHUB_CLIENT_ID |
| .env: CLIENT_SECRET | GOOGLE_CLIENT_SECRET | MICROSOFT_CLIENT_SECRET | GITHUB_CLIENT_SECRET |
| Auth URL | accounts.google.com | login.microsoftonline.com | github.com/login/oauth/authorize |
| Token URL | oauth2.googleapis.com | login.microsoftonline.com | github.com/login/oauth/access_token |
| Userinfo URL | openidconnect.googleapis.com | graph.microsoft.com | api.github.com/user |
| Protocol | OIDC | OIDC | OAuth2 (no id_token) |

## What's the same across all three?

```
_create_session()    → identical
Session cookie       → identical
/auth/me             → identical
/auth/logout         → identical
get_current_user()   → identical
Database tables      → identical
Frontend chat page   → identical
```

The only things that differ are the OAuth URLs, the credential names, and how the userinfo response is parsed (Google returns `email`, Microsoft returns `mail`, GitHub returns `login`).
