# Microsoft (Entra ID) OAuth Setup Guide

Get your Microsoft OAuth credentials to enable "Login with Microsoft" in the app.

**What you need by the end:**
- `MICROSOFT_CLIENT_ID`
- `MICROSOFT_CLIENT_SECRET`
- `MICROSOFT_TENANT` (usually `common`)
- Redirect URI configured: `http://localhost:8000/auth/microsoft/callback`

**Time:** ~5 minutes

## Step 1: Go to Azure Portal

Open **https://portal.azure.com**

Sign in with any Microsoft account (personal outlook.com or work account).

## Step 2: Navigate to App Registrations

1. In the top search bar, type **"App registrations"**
2. Click **App registrations** from the results
3. Click **+ New registration**

## Step 3: Register Your App

Fill in:
- **Name:** `AgentFlow`
- **Supported account types:** select the third option — **"Accounts in any organizational directory and personal Microsoft accounts"**
- **Redirect URI:**
  - Platform: select **Web** from the dropdown
  - URL: `http://localhost:8000/auth/microsoft/callback`

Click **Register**

## Step 4: Get Your Client ID

After registration, you're on the app's **Overview** page.

1. Find **Application (client) ID** — copy it
   - Looks like: `01878cba-05be-4ccb-b46a-7d3f42892a85`
2. Find **Directory (tenant) ID** — you can note this, but we'll use `common` instead

## Step 5: Create a Client Secret

1. In the left sidebar, click **Certificates & secrets**
2. Click **+ New client secret**
3. Fill in:
   - **Description:** `AgentFlow dev`
   - **Expires:** pick any option (6 months is fine for development)
4. Click **Add**
5. **Copy the Value column immediately** — you can only see it once
   - Looks like: `your-microsoft-client-secret-here`
   - Do NOT copy the "Secret ID" — that's not what you need

## Step 6: Add to .env

Open `.env` in the project root and paste:

```
MICROSOFT_CLIENT_ID=01878cba-05be-4ccb-b46a-7d3f42892a85
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret-here
MICROSOFT_TENANT=common
```

## Step 7: Test

```bash
python -m uvicorn app:app --reload --port 8000
cd frontend && npm run dev
```

1. Open `http://localhost:5173`
2. Click "Start chatting" then "Continue with Microsoft"
3. Microsoft login page appears
4. Sign in with any Microsoft account
5. You're redirected back, logged in

## Understanding the Tenant Setting

The `MICROSOFT_TENANT` controls who can log in:

| Value | Who can log in | Use when |
|-------|---------------|----------|
| `common` | Any Microsoft account (personal + work/school) | Development, consumer apps |
| `organizations` | Only work/school accounts (Azure AD) | Enterprise apps |
| `consumers` | Only personal accounts (outlook.com, hotmail.com) | Consumer apps |
| `your-tenant-id` | Only accounts in YOUR specific organization | Internal tools |

For development and teaching, `common` is the easiest — any Microsoft account works.

The tenant value gets inserted into the auth and token URLs:
```
Auth URL:  https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize
Token URL: https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token
```

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| "redirect_uri mismatch" | Redirect URI doesn't match | Go to Authentication in sidebar, check URI is exactly `http://localhost:8000/auth/microsoft/callback` |
| "AADSTS50011" | Redirect URI not registered | Add it: Authentication → Add a platform → Web → paste the URI |
| "invalid_client" | Wrong client secret | You may have copied the Secret ID instead of the Value. Generate a new secret. |
| "AADSTS700016" | App not found in tenant | Check the client ID is correct |
| "Need admin approval" | Your org requires admin consent | Use a personal Microsoft account instead, or ask your IT admin |

## How to Find Your App Later

Go to **https://portal.azure.com** → search **"App registrations"** → click **All applications** tab → click `AgentFlow`

From there you can:
- **Overview:** see Client ID, Tenant ID
- **Authentication:** manage redirect URIs, change account types
- **Certificates & secrets:** generate new secrets (old ones can't be viewed again)
- **API permissions:** see what scopes are granted
- **Owners:** who can manage this app

## What Microsoft Gives Us

| Field | Where it comes from |
|-------|-------------------|
| Email | `GET https://graph.microsoft.com/v1.0/me` → `mail` or `userPrincipalName` |
| Name | `displayName` |
| Profile picture | Requires separate call to `/me/photo/$value` (not implemented) |

Note: Microsoft's userinfo endpoint is the Graph API (`graph.microsoft.com/v1.0/me`), not a standard OIDC userinfo URL. The response fields are also different from Google — `mail` instead of `email`, `displayName` instead of `name`.
