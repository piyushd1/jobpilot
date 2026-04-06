"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
from src.api.routes import approvals, campaigns, feedback, manual_links, results, resume  # noqa: E402

app.include_router(resume.router)
app.include_router(campaigns.router)
app.include_router(results.router)
app.include_router(approvals.router)
app.include_router(feedback.router)
app.include_router(manual_links.router)

# WebSocket (if available)
try:
    from src.api.websocket import router as ws_router  # noqa: E402

    app.include_router(ws_router)
except ImportError:
    pass

# Export routes (if available)
try:
    from src.api.routes.export import router as export_router  # noqa: E402

    app.include_router(export_router)
except ImportError:
    pass


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env}
