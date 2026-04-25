# SSO Auth Basics

Learn authentication from scratch by building it into a real app. Start with sessions and cookies, then upgrade to Google OAuth. Same codebase, progressive complexity.

## What This Repo Teaches

| Concept | Where to learn |
|---------|---------------|
| How HTTP sessions work | `auth-workshop.ipynb` |
| How cookies carry identity | `auth-workshop.ipynb` |
| How login/logout works under the hood | `auth-workshop.ipynb` + Swagger UI |
| How to protect API routes | `auth/dependencies.py` |
| OAuth 2.0 vs OIDC | `concepts/05-oauth2-vs-oidc.md` |
| Google OAuth login flow | `google-oauth-workshop.ipynb` |
| How to set up Google Cloud credentials | `google-console-setup.ipynb` |

## Branches

| Branch | What it has | Auth method |
|--------|-----------|-------------|
| `main` | Chatbot only | No auth |
| `feature/google-auth` | Phase 1 | Simple email login (teaches sessions/cookies) |
| `feature/google-oauth` | Phase 2 | Google OAuth (same sessions, Google verifies identity) |

## Quick Start

### Phase 1: Email Login (sessions and cookies)

```bash
git checkout feature/google-auth
uv sync

# Terminal 1
python -m uvicorn app:app --reload --port 8000

# Terminal 2
cd frontend && npm install && npm run dev
```

Open `http://localhost:5173` and sign up with any email.

`.env` needs:
```
OPENAI_API_KEY=your-key
```

### Phase 2: Google OAuth

```bash
git checkout feature/google-oauth
uv sync

# Terminal 1
python -m uvicorn app:app --reload --port 8000

# Terminal 2
cd frontend && npm install && npm run dev
```

Open `http://localhost:5173` and click "Continue with Google".

`.env` needs:
```
OPENAI_API_KEY=your-key
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-secret
```

Get Google credentials by following `google-console-setup.ipynb`.

## Project Structure

```
.
├── app.py                      # FastAPI server (chat + auth routes)
├── agentic_rag.py              # Agentic RAG chatbot (LangChain + FAISS)
├── database.py                 # SQLAlchemy + SQLite setup
├── models.py                   # User and SessionRecord tables
├── config.py                   # Loads credentials from .env
├── auth/
│   ├── routes.py               # Login, logout, /me endpoints
│   └── dependencies.py         # get_current_user() gatekeeper
├── concepts/                   # Written explanations
│   ├── 01-what-is-oauth2-oidc.md
│   ├── 02-google-login-flow.md
│   ├── 03-sessions-and-cookies.md
│   ├── 04-code-mapping.md
│   └── 05-oauth2-vs-oidc.md
├── diagrams/                   # Visual diagrams (.drawio + .png)
│   ├── 01-session-lifecycle
│   ├── 02-login-flow-detailed
│   ├── 03-gatekeeper-flow
│   ├── 04-google-login-flow
│   └── 05-oauth2-vs-oidc
├── frontend/                   # React frontend (Vite)
├── auth-workshop.ipynb         # Interactive notebook: sessions and cookies
├── google-console-setup.ipynb  # Step-by-step: get Google credentials
├── google-oauth-workshop.ipynb # Interactive notebook: Google OAuth changes
└── .env                        # API keys (not committed)
```

## The Key Insight

Phase 1 and Phase 2 use the **exact same session mechanism**. The `_create_session()` function is character-for-character identical in both branches. The only thing that changes is how we verify the user's email:

- Phase 1: user types email (unverified)
- Phase 2: Google confirms email (verified)

Sessions, cookies, logout, route protection -- all stay the same.

## Tech Stack

- **Backend:** FastAPI + SQLAlchemy + SQLite
- **Auth:** authlib (Google OAuth), session cookies
- **AI:** LangChain + LangGraph + FAISS + OpenAI
- **Frontend:** React + Vite + Motion

## Diagrams

All diagrams are in `diagrams/` as editable `.drawio` files and exported `.png` files.

| Diagram | What it shows |
|---------|--------------|
| 01 Session Lifecycle | Swim lanes: signup, login, request, logout |
| 02 Login Flow | Step-by-step: what the login endpoint does |
| 03 Gatekeeper | Decision tree: how get_current_user() protects routes |
| 04 Google Login Flow | Swim lanes: browser, server, Google exchange |
| 05 OAuth2 vs OIDC | Side-by-side: authorization vs authentication |
