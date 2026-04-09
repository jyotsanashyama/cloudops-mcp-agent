"""
backend/main.py
FastAPI application — entry point for the backend server.
Wires together: lifespan, CORS, and routes.
"""

import sys
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, str(Path(__file__).parent))

from core.agent_manager import AgentManager
from routes.auth import router as auth_router
from routes.chat import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs ONCE on startup, ONCE on shutdown.
    Creates AgentManager and stores it in app.state so
    every route can access the same agent instance.
    """
    app.state.agent_manager = AgentManager()
    await app.state.agent_manager.initialise()
    yield
    print("Server shutting down.")


app = FastAPI(
    title="CloudOps MCP Agent API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # React (Create React App)
        "http://localhost:5173",   # React (Vite)
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)   # /auth/login
app.include_router(chat_router)   # /chat, /health