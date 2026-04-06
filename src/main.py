"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config.settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup and shutdown lifecycle."""
    # Startup
    # TODO: Initialize DB pool, Redis, Qdrant, MinIO client
    yield
    # Shutdown
    # TODO: Close connections


app = FastAPI(
    title="JobPilot",
    description="Autonomous multi-agent job hunting orchestrator",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env}
