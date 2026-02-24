"""FastAPI application factory."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import jobs, scrape, sources


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    print(f"Starting req-hunter in {settings.app_env} mode")
    yield
    from app.database import engine

    await engine.dispose()


app = FastAPI(
    title="req-hunter",
    description="Job listing scraper and aggregator API",
    version="0.1.0",
    lifespan=lifespan,
    debug=settings.app_debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.app_debug else [],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs.router, prefix="/api/v1")
app.include_router(sources.router, prefix="/api/v1")
app.include_router(scrape.router, prefix="/api/v1")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok", "env": settings.app_env}
