# Google Cloud Console Setup Guide

Get your OAuth credentials to enable "Login with Google" in the app.

**What you need by the end:**
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- Redirect URI configured: `http://localhost:8000/auth/callback`

**Time:** ~10 minutes

## Step 1: Go to Google Cloud Console

Open **https://console.cloud.google.com** and sign in with your Google account.

## Step 2: Create a New Project

1. Click the **project dropdown** at the top of the page (next to "Google Cloud")
2. Click **"New Project"** in the top right of the popup
3. Fill in:
   - **Project name:** `AgentFlow` (or any name you like)
   - **Organization:** leave as default
4. Click **"Create"**
5. Wait a few seconds, then **select the new project** from the dropdown

## Step 3: Configure the OAuth Consent Screen

1. In the left sidebar, go to **APIs & Services > OAuth consent screen**
2. Click **"Get Started"** or **"Configure Consent Screen"**
3. Choose User Type: **External** (allows any Google account)
4. Click **"Create"**

You'll see tabs at the top: **Branding | Audience | Data Access**

**Branding tab:**
1. Fill in:
   - **App name:** `AgentFlow`
   - **User support email:** select your email
   - **Developer contact email:** your email
2. Click **"Save"**

**Audience tab:**
1. Under User type, make sure **External** is selected
2. Under **Test users**, click **"Add Users"**
3. Add your own Gmail address (and any students who need to test)
4. Click **"Save"**

Note: While in "Testing" mode, only test users can log in. This is fine for development.

**Data Access tab (this is where scopes live):**
1. Click **"Add or Remove Scopes"**
2. From the list, check these **three**:
   - `openid` — "Associate you with your personal info on Google"
   - `.../auth/userinfo.email` — "See your primary Google Account email address"
   - `.../auth/userinfo.profile` — "See your personal info..."
3. Ignore everything else (BigQuery, Analytics, etc.)
4. Click **"Update"** then **"Save"**

## Step 4: Create OAuth 2.0 Credentials

1. In the left sidebar, go to **APIs & Services > Credentials**
2. Click **"+ Create Credentials"** at the top
3. Select **"OAuth client ID"**
4. Fill in:
   - **Application type:** `Web application`
   - **Name:** `AgentFlow Web`
5. Under **"Authorized redirect URIs":**
   - Click **"+ Add URI"**
   - Enter exactly: `http://localhost:8000/auth/callback`
6. Click **"Create"**

A popup appears with:
- **Client ID:** something like `123456789-abcdef.apps.googleusercontent.com`
- **Client Secret:** something like `GOCSPX-abcdefgh123456`

**Copy both values.**

## Step 5: Add to .env

Open `.env` in the project root and add:

```
GOOGLE_CLIENT_ID=paste-your-client-id-here
GOOGLE_CLIENT_SECRET=paste-your-secret-here
```

## Step 6: Test

```bash
python -m uvicorn app:app --reload --port 8000
cd frontend && npm run dev
```

1. Open `http://localhost:5173`
2. Click "Start chatting" then "Continue with Google"
3. Google login page should appear
4. Sign in and you're redirected back, logged in

**If you see "redirect_uri_mismatch":** Go back to Google Console > Credentials > edit your OAuth client > check the redirect URI is exactly `http://localhost:8000/auth/callback` (no trailing slash, no https).

## Quick Reference

| Thing | Where it lives |
|-------|---------------|
| Project | Google Cloud Console |
| OAuth Consent Screen | APIs & Services > OAuth consent screen |
| Client ID | APIs & Services > Credentials |
| Client Secret | APIs & Services > Credentials |
| Redirect URI | Inside the OAuth Client config |
| Test users | OAuth consent screen > Test users |

```
Where credentials end up in code:

.env                    GOOGLE_CLIENT_ID=...
                        GOOGLE_CLIENT_SECRET=...
                              |
config.py               os.getenv("GOOGLE_CLIENT_ID")
                        os.getenv("GOOGLE_CLIENT_SECRET")
                              |
auth/routes.py          OAuth2Session(client_id=..., client_secret=...)
```
