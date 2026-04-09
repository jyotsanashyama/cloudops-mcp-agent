"""
routes/auth.py
This is an HTTP layer that sits on top of "core/auth.py"

workflow:
- receives HTTP POST requets from browser
- extract username nad password frfo json body
- calls core/auth.py functions
- returns HTTP response with the token

POST /auth/login  →  returns JWT token if credentials are correct
"""

from fastapi import APIRouter, HTTPException, status
from core.models import LoginRequest, LoginResponse
from core.auth import verify_credentials, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest):
    """
    Takes username + password.
    Returns a JWT token if credentials match .env values.
    Returns 401 if credentials are wrong.
    This function itself has ZERO auth logic —
    it just calls core/auth.py and formats the response.
    """
    if not verify_credentials(request.username, request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    token = create_access_token(request.username)
    return LoginResponse(access_token=token)