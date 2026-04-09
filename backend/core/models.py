"""
core/models.py
Pydantic models for all request and response bodies.
These define the exact JSON shape the API accepts and returns.
"""

from pydantic import BaseModel
from typing import Optional


# ── Auth models ──────────────────────────────────────────────

class LoginRequest(BaseModel):
    """What the frontend sends to POST /auth/login"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """What we send back after successful login"""
    access_token: str
    token_type: str = "bearer"


# ── Chat models ──────────────────────────────────────────────

class ChatRequest(BaseModel):
    """What the frontend sends to POST /chat"""
    message: str
    thread_id: Optional[str] = None   # if None, backend generates one


class ChatResponse(BaseModel):
    """What we send back after agent processes the question"""
    answer: str
    thread_id: str    # frontend stores this to continue the conversation


# ── Health model ─────────────────────────────────────────────

class HealthResponse(BaseModel):
    """What GET /health returns"""
    status: str
    tools_available: int