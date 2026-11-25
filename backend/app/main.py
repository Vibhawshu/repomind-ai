from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings  # noqa: F401
from app.api.routes import health, repositories, chat

app = FastAPI(
    title="RepoMind AI",
    description="Intelligent Codebase Understanding and Repository Analysis Assistant",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(repositories.router, prefix="/api", tags=["repositories"])
app.include_router(chat.router, prefix="/api", tags=["chat"])