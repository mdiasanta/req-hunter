"""Source management endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Source
from app.schemas import SourceCreate, SourceListResponse, SourceRead, SourceUpdate

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("/", response_model=SourceListResponse)
async def list_sources(db: AsyncSession = Depends(get_db)) -> SourceListResponse:
    """Return all configured scrape sources."""
    total = await db.scalar(select(func.count()).select_from(Source))
    result = await db.execute(select(Source).order_by(Source.created_at.desc()))
    sources = result.scalars().all()
    return SourceListResponse(total=total or 0, items=list(sources))


@router.post("/", response_model=SourceRead, status_code=201)
async def create_source(
    payload: SourceCreate,
    db: AsyncSession = Depends(get_db),
) -> Source:
    """Add a new website to scrape with an associated keyword."""
    source = Source(**payload.model_dump())
    db.add(source)
    await db.flush()
    await db.refresh(source)
    return source


@router.get("/{source_id}", response_model=SourceRead)
async def get_source(source_id: int, db: AsyncSession = Depends(get_db)) -> Source:
    """Return a single source by ID."""
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source


@router.patch("/{source_id}", response_model=SourceRead)
async def update_source(
    source_id: int,
    payload: SourceUpdate,
    db: AsyncSession = Depends(get_db),
) -> Source:
    """Update a source's configuration or toggle it active/inactive."""
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    data = payload.model_dump(exclude_none=True)
    clear_blocked = bool(data.pop("clear_blocked", False))
    for field, value in data.items():
        setattr(source, field, value)
    if clear_blocked:
        source.is_blocked = False
        source.blocked_reason = None
        source.blocked_at = None
        source.last_error = None
        source.is_active = True
    await db.flush()
    await db.refresh(source)
    return source


@router.delete("/{source_id}", status_code=204)
async def delete_source(source_id: int, db: AsyncSession = Depends(get_db)) -> None:
    """Delete a source permanently."""
    source = await db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    await db.delete(source)
    await db.flush()
