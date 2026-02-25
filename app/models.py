"""SQLAlchemy ORM models for req-hunter."""

import enum
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class JobStatus(str, enum.Enum):
    NEW = "new"
    SEEN = "seen"
    APPLIED = "applied"
    REJECTED = "rejected"
    IGNORED = "ignored"


class Job(Base):
    """Represents a single job listing scraped from an external source."""

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    company: Mapped[str] = mapped_column(String(256), nullable=False)
    location: Mapped[str | None] = mapped_column(String(256), nullable=True)
    url: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus), default=JobStatus.NEW, nullable=False
    )
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Source(Base):
    """A website to scrape for job listings, with an associated search keyword."""

    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    base_url: Mapped[str] = mapped_column(Text, nullable=False)
    keyword: Mapped[str] = mapped_column(String(256), nullable=False)
    query_param: Mapped[str] = mapped_column(String(64), default="q", nullable=False)
    url_path_filter: Mapped[str | None] = mapped_column(String(256), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    blocked_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    blocked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_scraped_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ScrapeSchedule(Base):
    """Configuration for automatic scrape runs."""

    __tablename__ = "scrape_schedules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    interval_minutes: Mapped[int] = mapped_column(default=60, nullable=False)
    last_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    next_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
