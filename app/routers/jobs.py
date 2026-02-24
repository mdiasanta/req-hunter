"""Job listing CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Job, JobStatus
from app.schemas import JobListResponse, JobRead, JobUpdate

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    status: JobStatus | None = Query(None, description="Filter by job status"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> JobListResponse:
    """Return a paginated list of scraped job listings."""
    query = select(Job)
    count_query = select(func.count()).select_from(Job)

    if status:
        query = query.where(Job.status == status)
        count_query = count_query.where(Job.status == status)

    total = await db.scalar(count_query)
    result = await db.execute(query.offset(offset).limit(limit))
    jobs = result.scalars().all()

    return JobListResponse(total=total or 0, items=list(jobs))


@router.get("/{job_id}", response_model=JobRead)
async def get_job(job_id: int, db: AsyncSession = Depends(get_db)) -> Job:
    """Return a single job by ID."""
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.patch("/{job_id}", response_model=JobRead)
async def update_job_status(
    job_id: int,
    payload: JobUpdate,
    db: AsyncSession = Depends(get_db),
) -> Job:
    """Update a job's status (e.g., mark as applied or ignored)."""
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    job.status = payload.status
    await db.flush()
    await db.refresh(job)
    return job
