"""
FastAPI wrapper for the Agentic RAG chatbot.

Run:  uvicorn app:app --reload
Test: curl -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"question": "What is RAG?"}'
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from agentic_rag import ask

app = FastAPI(title="Agentic RAG Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str


class ChatResponse(BaseModel):
    question: str
    answer: str


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    answer = ask(req.question)
    return ChatResponse(question=req.question, answer=answer)
