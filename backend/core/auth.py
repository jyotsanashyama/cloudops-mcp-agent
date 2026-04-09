"""
core/auth.py
JWT token creation and verification.
Also handles checking username/password against .env credentials.
Contains pure Python logic. No HTTP, no routes, no FastAPI. Just functions
These functions don't know anything about HTTP requests. They just take inputs and return outputs. You could call them from anywhere — a CLI, a test, a route

"""

import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from pathlib import Path
from jose import jwt, JWTError
from fastapi import HTTPException, status

# Load .env from mcp-server folder (single source of truth)
load_dotenv(Path(__file__).parent.parent.parent / "mcp-server" / ".env")

# ── Config ────────────────────────────────────────────────────────
# Secret key used to sign JWT tokens.
# Anyone with this key can create valid tokens, so keep it secret.
SECRET_KEY = os.getenv("JWT_SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY is not set in .env — server cannot start")

ALGORITHM = "HS256"           # signing algorithm
TOKEN_EXPIRE_HOURS = 24       # token valid for 24 hours


# ── Credential check ──────────────────────────────────────────────
def verify_credentials(username: str, password: str) -> bool:
    """
    Check username and password against values stored in .env
    In a real app this would query a database.
    For portfolio: one admin user defined in .env is enough.
    """
    valid_username = os.getenv("ADMIN_USERNAME")
    valid_password = os.getenv("ADMIN_PASSWORD")
    
    if not valid_username or not valid_password:
        raise RuntimeError("ADMIN_USERNAME or ADMIN_PASSWORD not set in .env")
    
    return username == valid_username and password == valid_password


# ── Token creation ────────────────────────────────────────────────
def create_access_token(username: str) -> str:
    """
    Create a signed JWT token for the given username.
    The token contains:
      - sub: the username (subject)
      - exp: expiry timestamp (24 hours from now)
    """
    payload = {
        "sub": username,
        "exp": datetime.now(timezone.utc) + timedelta(hours=TOKEN_EXPIRE_HOURS)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# ── Token verification ────────────────────────────────────────────
def verify_access_token(token: str) -> str:
    """
    Verify a JWT token and return the username inside it.
    Raises HTTP 401 if the token is invalid or expired.
    This function is called on every protected request.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        return username
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is invalid or expired"
        )
