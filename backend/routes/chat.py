"""
routes/chat.py
exposes:
POST /chat         →  send message, get agent answer
GET  /health       →  check server + agent status

workflow:
- Receives POST /chat with a message and token in the header
- Calls verify_access_token() from core/auth.py to check the token
- Calls agent_manager.chat() to run the agent
- Returns the answer
"""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.models import ChatRequest, ChatResponse, HealthResponse
from core.auth import verify_access_token

router = APIRouter(tags=["chat"])
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Dependency that extracts and verifies the JWT token
    from the Authorization header on every protected request.
    Usage: add  current_user = Depends(get_current_user)
    to any route that requires login.
    """
    return verify_access_token(credentials.credentials)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    http_request: Request,
    current_user: str = Depends(get_current_user),   # ← requires valid token
):
    """
    Main chat endpoint.
    - Requires valid JWT token in Authorization header
    - If thread_id not provided, generates a new one (new conversation)
    - If thread_id provided, continues existing conversation (memory)
    - Passes message to agent, returns answer
    """
    agent_manager = http_request.app.state.agent_manager

    if not agent_manager.ready:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent is still initialising, try again in a moment"
        )

    # Generate thread_id if not provided by frontend
    thread_id = request.thread_id or str(uuid.uuid4())

    try:
        answer = await agent_manager.chat(
            message=request.message,
            thread_id=thread_id,
        )
        return ChatResponse(answer=answer, thread_id=thread_id)

    except Exception as e:
        error_str = str(e).lower()

        if "api key" in error_str or "401" in error_str:
            detail = "Authentication error with AI provider. Check GROQ_API_KEY."
        elif "rate limit" in error_str or "429" in error_str:
            detail = "Rate limit hit. Please wait a moment and try again."
        elif "timeout" in error_str:
            detail = "Request timed out. Try again."
        else:
            detail = f"Agent error: {str(e)}"

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


@router.get("/health", response_model=HealthResponse)
async def health(http_request: Request):
    """
    Health check — no auth required.
    Returns whether the agent is ready and how many tools are loaded.
    """
    agent_manager = http_request.app.state.agent_manager
    return HealthResponse(
        status="ok" if agent_manager.ready else "initialising",
        tools_available=len(agent_manager.tools)
    )