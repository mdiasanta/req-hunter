"""Pydantic schemas for request validation and response serialization."""

from datetime import datetime

from pydantic import BaseModel, HttpUrl

from app.models import JobStatus


# ── Source schemas ─────────────────────────────────────────────────────────────

class SourceBase(BaseModel):
    name: str
    base_url: str
    keyword: str
    query_param: str = "q"
    url_path_filter: str | None = None


class SourceCreate(SourceBase):
    """Schema for creating a new scrape source."""


class SourceUpdate(BaseModel):
    """Schema for partially updating a source."""

    name: str | None = None
    base_url: str | None = None
    keyword: str | None = None
    query_param: str | None = None
    url_path_filter: str | None = None
    is_active: bool | None = None


class SourceRead(SourceBase):
    """Schema returned by source API endpoints."""

    id: int
    is_active: bool
    last_scraped_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class SourceListResponse(BaseModel):
    total: int
    items: list[SourceRead]


# ── Scrape result schema ───────────────────────────────────────────────────────

class ScrapeResult(BaseModel):
    sources_processed: int
    jobs_found: int
    jobs_new: int
    errors: list[str] = []


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
