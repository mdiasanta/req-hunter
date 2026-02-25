"""Background scheduler for recurring scrape runs."""

import asyncio
from datetime import datetime, timedelta, timezone
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models import ScrapeSchedule
from app.scraper.runner import run_all_sources

logger = logging.getLogger(__name__)
_POLL_INTERVAL_SECONDS = 20
_MIN_INTERVAL_MINUTES = 5


async def ensure_schedule_row(db: AsyncSession) -> ScrapeSchedule:
    """Return the singleton schedule row, creating one if it doesn't exist."""
    result = await db.execute(
        select(ScrapeSchedule).order_by(ScrapeSchedule.id.asc()).limit(1)
    )
    schedule = result.scalar_one_or_none()
    if schedule is None:
        schedule = ScrapeSchedule(
            is_enabled=False,
            interval_minutes=60,
            next_run_at=None,
        )
        db.add(schedule)
        await db.flush()
    return schedule


def normalize_interval(minutes: int) -> int:
    return max(_MIN_INTERVAL_MINUTES, minutes)


def calculate_next_run(now_utc: datetime, interval_minutes: int) -> datetime:
    return now_utc + timedelta(minutes=normalize_interval(interval_minutes))


class ScrapeScheduler:
    def __init__(self) -> None:
        self._task: asyncio.Task[None] | None = None
        self._is_running_scrape = False

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._task = asyncio.create_task(self._loop(), name="scrape-scheduler-loop")
        logger.info("Scrape scheduler started")

    async def stop(self) -> None:
        if not self._task:
            return
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        logger.info("Scrape scheduler stopped")

    async def _loop(self) -> None:
        while True:
            try:
                await self._tick()
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Unexpected scheduler loop error")
            await asyncio.sleep(_POLL_INTERVAL_SECONDS)

    async def _tick(self) -> None:
        if self._is_running_scrape:
            return

        now_utc = datetime.now(timezone.utc)
        async with AsyncSessionLocal() as db:
            schedule = await ensure_schedule_row(db)

            if not schedule.is_enabled:
                await db.commit()
                return

            if schedule.next_run_at is None:
                schedule.next_run_at = calculate_next_run(
                    now_utc=now_utc,
                    interval_minutes=schedule.interval_minutes,
                )
                await db.commit()
                return

            if schedule.next_run_at > now_utc:
                await db.commit()
                return

            self._is_running_scrape = True
            try:
                logger.info("Scheduled scrape started")
                result = await run_all_sources(db)
                schedule.last_run_at = datetime.now(timezone.utc)
                schedule.next_run_at = calculate_next_run(
                    now_utc=schedule.last_run_at,
                    interval_minutes=schedule.interval_minutes,
                )
                await db.commit()
                logger.info(
                    "Scheduled scrape finished: sources=%s found=%s new=%s errors=%s",
                    result.sources_processed,
                    result.jobs_found,
                    result.jobs_new,
                    len(result.errors),
                )
                for err in result.errors:
                    logger.error("Scheduled scrape error: %s", err)
            except Exception:
                await db.rollback()
                logger.exception("Scheduled scrape failed")
            finally:
                self._is_running_scrape = False


scrape_scheduler = ScrapeScheduler()
