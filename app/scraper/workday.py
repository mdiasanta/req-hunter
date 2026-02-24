"""Workday ATS scraper using the undocumented internal search API.

All myworkdayjobs.com tenants expose a consistent REST endpoint at:
  POST https://{tenant}.wd{n}.myworkdayjobs.com/wday/cxs/{tenant}/{jobsite}/jobs

This endpoint is the same one the public job board JavaScript calls, so the
request looks identical to a normal browser visit. No authentication is required
for public job boards.

Rate-limiting notes:
- Keep SCRAPER_DELAY_SECONDS >= 2 between pagination requests.
- Running once or twice per day per source is well within safe limits.
"""

import asyncio
import re
from urllib.parse import urlparse

import httpx

from app.config import settings
from app.schemas import JobCreate

_LOCALE_RE = re.compile(r"^[a-z]{2}-[A-Z]{2}$")


def _parse_workday_url(url: str) -> tuple[str, str, str]:
    """Return (api_base, tenant, jobsite) extracted from a Workday board URL.

    Example:
        https://acme.wd5.myworkdayjobs.com/en-US/External
        → ("https://acme.wd5.myworkdayjobs.com", "acme", "External")
    """
    parsed = urlparse(url)
    hostname = parsed.hostname or ""
    tenant = hostname.split(".")[0]

    path_parts = [p for p in parsed.path.strip("/").split("/") if p]
    # Strip locale segments like "en-US", "de-DE"
    non_locale = [p for p in path_parts if not _LOCALE_RE.match(p)]
    jobsite = non_locale[0] if non_locale else "careers"

    api_base = f"{parsed.scheme}://{hostname}"
    return api_base, tenant, jobsite


class WorkdayScraper:
    """Scrapes a Workday ATS job board via its internal search API (no browser needed)."""

    def __init__(self, source_name: str, base_url: str, keyword: str) -> None:
        self._source_name = source_name
        self._base_url = base_url
        self._keyword = keyword
        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self) -> "WorkdayScraper":
        self._client = httpx.AsyncClient(
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json",
                "Content-Type": "application/json",
                # Referer makes the request look like it came from the job board page
                "Referer": self._base_url,
            },
            timeout=settings.scraper_timeout_seconds,
        )
        return self

    async def __aexit__(self, *args: object) -> None:
        if self._client:
            await self._client.aclose()

    async def scrape(self) -> list[JobCreate]:
        if self._client is None:
            raise RuntimeError("Use `async with WorkdayScraper(...)` context manager.")

        api_base, tenant, jobsite = _parse_workday_url(self._base_url)
        api_url = f"{api_base}/wday/cxs/{tenant}/{jobsite}/jobs"

        jobs: list[JobCreate] = []
        offset = 0
        limit = 20

        while True:
            response = await self._client.post(
                api_url,
                json={
                    "appliedFacets": {},
                    "limit": limit,
                    "offset": offset,
                    "searchText": self._keyword,
                },
            )
            response.raise_for_status()
            data = response.json()

            postings = data.get("jobPostings", [])
            if not postings:
                break

            for posting in postings:
                external_path = posting.get("externalPath", "")
                job_url = f"{api_base}{external_path}"
                jobs.append(
                    JobCreate(
                        title=posting.get("title", "Unknown"),
                        company=self._source_name,
                        location=posting.get("locationsText"),
                        url=job_url,
                        source=self._source_name,
                    )
                )

            offset += limit
            if offset >= data.get("total", 0):
                break

            await asyncio.sleep(settings.scraper_delay_seconds)

        return jobs
