"""Endpoints for viewing application logs."""

from fastapi import APIRouter, Query

from app.logging_utils import tail_log_lines

router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("/")
async def get_logs(
    limit: int = Query(default=200, ge=1, le=2000),
) -> dict[str, object]:
    """Return the most recent application log lines."""
    lines = tail_log_lines(limit)
    return {
        "total": len(lines),
        "items": lines,
    }
