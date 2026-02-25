"""Scheduler configuration endpoints."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import ScheduleRead, ScheduleUpdate
from app.scheduler import (
    calculate_next_run,
    ensure_schedule_row,
    normalize_interval,
)

router = APIRouter(prefix="/schedule", tags=["schedule"])


@router.get("/", response_model=ScheduleRead)
async def get_schedule(db: AsyncSession = Depends(get_db)) -> ScheduleRead:
    schedule = await ensure_schedule_row(db)
    return ScheduleRead.model_validate(schedule)


@router.patch("/", response_model=ScheduleRead)
async def update_schedule(
    payload: ScheduleUpdate,
    db: AsyncSession = Depends(get_db),
) -> ScheduleRead:
    schedule = await ensure_schedule_row(db)
    now_utc = datetime.now(timezone.utc)

    if payload.interval_minutes is not None:
        schedule.interval_minutes = normalize_interval(payload.interval_minutes)

    if payload.is_enabled is not None:
        schedule.is_enabled = payload.is_enabled

    if schedule.is_enabled:
        schedule.next_run_at = calculate_next_run(
            now_utc=now_utc,
            interval_minutes=schedule.interval_minutes,
        )
    else:
        schedule.next_run_at = None

    await db.flush()
    await db.refresh(schedule)
    return ScheduleRead.model_validate(schedule)
