# GitHub OAuth App Setup Guide

Get your GitHub OAuth credentials to enable "Login with GitHub" in the app.

**What you need by the end:**
- `GITHUB_CLIENT_ID`
- `GITHUB_CLIENT_SECRET`
- Callback URL configured: `http://localhost:8000/auth/github/callback`

**Time:** ~3 minutes

## Step 1: Go to GitHub Developer Settings

Open **https://github.com/settings/developers**

Sign in with your GitHub account if prompted.

## Step 2: Create a New OAuth App

1. Click **OAuth Apps** in the left sidebar
2. Click **New OAuth App**
3. Fill in:
   - **Application name:** `AgentFlow`
   - **Homepage URL:** `http://localhost:5173`
   - **Authorization callback URL:** `http://localhost:8000/auth/github/callback`
4. Click **Register application**

## Step 3: Get Your Credentials

After registration, you'll land on the app's settings page.

1. **Client ID** is shown at the top — copy it
   - Looks like: `Ov23liAtqZpS6B9dIUaE`
2. Click **Generate a new client secret**
3. **Copy the secret immediately** — you won't be able to see it again
   - Looks like: `your-github-client-secret-here`

## Step 4: Add to .env

Open `.env` in the project root and paste:

```
GITHUB_CLIENT_ID=Ov23lixxxxxxxxxxxxxxxxxx
GITHUB_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Step 5: Test

```bash
python -m uvicorn app:app --reload --port 8000
cd frontend && npm run dev
```

1. Open `http://localhost:5173`
2. Click "Start chatting" then "Continue with GitHub"
3. GitHub asks you to authorize the app
4. You're redirected back, logged in with your GitHub name and avatar

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| "redirect_uri mismatch" | Callback URL doesn't match | Go to app settings, check it's exactly `http://localhost:8000/auth/github/callback` |
| No email returned | GitHub email is set to private | The code handles this by calling `/user/emails` API as fallback |
| "Bad credentials" | Wrong client secret | Generate a new secret, paste again |

## How to find your app later

Go to **https://github.com/settings/developers** → **OAuth Apps** → click on `AgentFlow`

From there you can:
- View/copy the Client ID
- Generate a new client secret (old one stops working)
- Update the callback URL
- See how many users have authorized the app
- Delete the app

## What GitHub gives us

| Field | Where it comes from |
|-------|-------------------|
| Email | `GET https://api.github.com/user` or `/user/emails` if private |
| Name | `user.name` (display name) or `user.login` (username) as fallback |
| Avatar | `user.avatar_url` |

## GitHub vs Google vs Microsoft

| | GitHub | Google | Microsoft |
|---|---|---|---|
| Protocol | OAuth 2.0 only | OIDC | OIDC |
| ID token | No | Yes | Yes |
| Discovery | No `.well-known` | Yes | Yes |
| Token endpoint | Needs `Accept: application/json` header | Standard | Standard |
| Email privacy | User can hide email | Always returned | Always returned |
| Setup time | ~3 minutes | ~10 minutes | ~5 minutes |
| Scopes | `read:user user:email` | `openid email profile` | `openid email profile User.Read` |
