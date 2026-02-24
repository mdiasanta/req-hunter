"""Orchestrates scraper runs across configured sources.

The dispatcher inspects each source URL and routes it to the right scraper:
  - myworkdayjobs.com  →  WorkdayScraper  (API-based, no browser)
  - everything else    →  GenericScraper  (Playwright heuristic)
"""

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Job, JobStatus, Source
from app.schemas import JobCreate, ScrapeResult
from app.scraper.generic import GenericScraper
from app.scraper.workday import WorkdayScraper


def _is_workday(url: str) -> bool:
    return "myworkdayjobs.com" in url.lower()


def _build_scraper(source: Source) -> GenericScraper | WorkdayScraper:
    if _is_workday(source.base_url):
        return WorkdayScraper(
            source_name=source.name,
            base_url=source.base_url,
            keyword=source.keyword,
        )
    return GenericScraper(
        source_name=source.name,
        base_url=source.base_url,
        keyword=source.keyword,
        query_param=source.query_param,
        url_path_filter=source.url_path_filter,
    )


async def _save_new_jobs(jobs: list[JobCreate], db: AsyncSession) -> int:
    """Insert jobs that don't already exist (deduped by URL). Returns count inserted."""
    new_count = 0
    for job in jobs:
        url_str = str(job.url)
        existing = await db.scalar(select(Job).where(Job.url == url_str))
        if existing is None:
            db.add(
                Job(
                    title=job.title,
                    company=job.company,
                    location=job.location,
                    url=url_str,
                    description=job.description,
                    source=job.source,
                    status=JobStatus.NEW,
                )
            )
            new_count += 1
    await db.flush()
    return new_count


async def run_source(
    source: Source, db: AsyncSession
) -> tuple[int, int, list[str]]:
    """Run scraper for a single source. Returns (jobs_found, jobs_new, errors)."""
    errors: list[str] = []
    jobs_found = 0
    jobs_new = 0

    scraper = _build_scraper(source)
    try:
        async with scraper:
            jobs = await scraper.scrape()
        jobs_found = len(jobs)
        jobs_new = await _save_new_jobs(jobs, db)
        source.last_scraped_at = datetime.now(timezone.utc)
        await db.flush()
    except Exception as exc:
        errors.append(f"[{source.name}] {exc}")

    return jobs_found, jobs_new, errors


async def run_all_sources(db: AsyncSession) -> ScrapeResult:
    """Run scrapers for all active sources and return aggregated stats."""
    result = await db.execute(select(Source).where(Source.is_active.is_(True)))
    sources = list(result.scalars().all())

    total_found = 0
    total_new = 0
    all_errors: list[str] = []

    for source in sources:
        found, new, errors = await run_source(source, db)
        total_found += found
        total_new += new
        all_errors.extend(errors)

    return ScrapeResult(
        sources_processed=len(sources),
        jobs_found=total_found,
        jobs_new=total_new,
        errors=all_errors,
    )
