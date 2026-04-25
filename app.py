"""
FastAPI wrapper for the Agentic RAG chatbot + Google Auth.

Run:  python -m uvicorn app:app --reload
Test: curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"question": "What is RAG?"}'
"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agentic_rag import ask
from auth.routes import router as auth_router
from auth.dependencies import get_current_user
from database import engine, Base
from models import User

# Create all tables on startup (User, SessionRecord)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AgentFlow")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,          # IMPORTANT: allows cookies cross-origin
    allow_methods=["*"],
    allow_headers=["*"],
)

# Wire in auth routes: /auth/google/login, /auth/callback, /auth/logout, /auth/me
app.include_router(auth_router)


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    question: str
    answer: str


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, user: User = Depends(get_current_user)):
    """Protected endpoint — only logged-in users can chat."""
    answer = ask(req.question)
    return ChatResponse(question=req.question, answer=answer)
