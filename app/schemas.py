"""Pydantic schemas for request validation and response serialization."""

from datetime import datetime

from pydantic import BaseModel, HttpUrl

from app.models import JobStatus


class JobBase(BaseModel):
    title: str
    company: str
    location: str | None = None
    url: HttpUrl
    description: str | None = None
    source: str


class JobCreate(JobBase):
    """Schema for creating a new job (used internally by the scraper)."""


class JobUpdate(BaseModel):
    """Schema for updating a job's status."""

    status: JobStatus


class JobRead(JobBase):
    """Schema returned by API endpoints."""

    id: int
    status: JobStatus
    scraped_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    """Paginated list of jobs."""

    total: int
    items: list[JobRead]
