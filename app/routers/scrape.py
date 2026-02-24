"""Endpoints for triggering scraper runs."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Source
from app.schemas import ScrapeResult
from app.scraper.runner import run_all_sources, run_source

router = APIRouter(prefix="/scrape", tags=["scrape"])


@router.post("/run", response_model=ScrapeResult)
async def scrape_all(db: AsyncSession = Depends(get_db)) -> ScrapeResult:
    """Trigger a scrape run across all active sources."""
    return await run_all_sources(db)


@router.post("/run/{source_id}", response_model=ScrapeResult)
async def scrape_one(
    source_id: int,
    db: AsyncSession = Depends(get_db),
) -> ScrapeResult:
    """Trigger a scrape run for a single source by ID."""
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    found, new, errors = await run_source(source, db)
    return ScrapeResult(
        sources_processed=1,
        jobs_found=found,
        jobs_new=new,
        errors=errors,
    )
