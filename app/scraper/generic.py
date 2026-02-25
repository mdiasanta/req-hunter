"""Generic Playwright-based scraper for arbitrary job boards.

Navigates to `{base_url}?{query_param}={keyword}`, waits for the page to
settle, then extracts links whose URLs look like individual job postings.

This works well for simple job boards (custom career pages, Lever, Greenhouse,
etc.). For Workday ATS sites use WorkdayScraper instead.
"""

import logging
from urllib.parse import quote_plus, urljoin

from app.schemas import JobCreate
from app.scraper.base import BaseScraper

logger = logging.getLogger(__name__)

# URL path fragments that strongly suggest a job-specific page
_JOB_URL_FRAGMENTS = frozenset(
    {
        "/job/",
        "/jobs/",
        "/career/",
        "/careers/",
        "/position/",
        "/positions/",
        "/opening/",
        "/openings/",
        "/posting/",
        "/postings/",
        "/requisition/",
        "/vacancy/",
        "/vacancies/",
        "/role/",
        "/roles/",
    }
)

_MIN_TITLE_LEN = 5
_MAX_TITLE_LEN = 150
_MAX_PAGES = 30
_MAX_STALE_PAGES = 2


class GenericScraper(BaseScraper):
    """Heuristic scraper that extracts job links from an arbitrary job board page."""

    def __init__(
        self,
        source_name: str,
        base_url: str,
        keyword: str,
        query_param: str = "q",
        url_path_filter: str | None = None,
    ) -> None:
        super().__init__()
        self.source = source_name
        self._source_name = source_name
        self._base_url = base_url
        self._keyword = keyword
        self._query_param = query_param
        self._url_path_filter = url_path_filter.lower() if url_path_filter else None

    def _build_url(self) -> str:
        sep = "&" if "?" in self._base_url else "?"
        return f"{self._base_url}{sep}{self._query_param}={quote_plus(self._keyword)}"

    def _looks_like_job_url(self, href: str) -> bool:
        href_lower = href.lower()
        if self._url_path_filter:
            return self._url_path_filter in href_lower
        return any(frag in href_lower for frag in _JOB_URL_FRAGMENTS)

    async def _wait_for_page_settle(self) -> None:
        try:
            await self.page.wait_for_load_state("networkidle", timeout=10_000)
        except Exception:
            pass  # Proceed with whatever is rendered

    async def _detect_antibot_block(self) -> None:
        title = (await self.page.title()).lower()
        body_text = (await self.page.locator("body").inner_text()).lower()
        if (
            "cloudflare" in title
            or "cloudflare" in body_text
            or "attention required" in title
            or "just a moment" in title
            or "verify you are human" in body_text
        ):
            message = (
                "Blocked by anti-bot challenge (Cloudflare). "
                "Try headful mode or a different network/IP."
            )
            logger.warning("%s URL=%s", message, self.page.url)
            raise RuntimeError(message)

    async def _active_page_token(self) -> str | None:
        active = self.page.locator("ul.pagination li.page-item.active").first
        if await active.count() == 0:
            return None
        text = (await active.inner_text()).strip()
        return text or None

    async def _collect_jobs_from_current_page(
        self,
        seen_urls: set[str],
        jobs: list[JobCreate],
    ) -> int:
        page_url = self.page.url
        links = await self.page.locator("a[href]").all()
        added = 0

        for link in links:
            try:
                href = await link.get_attribute("href") or ""
                text = (await link.inner_text()).strip()
            except Exception:
                continue

            if not self._looks_like_job_url(href):
                continue

            if not text or len(text) < _MIN_TITLE_LEN or len(text) > _MAX_TITLE_LEN:
                continue

            absolute_url = urljoin(page_url, href)
            if absolute_url in seen_urls:
                continue
            seen_urls.add(absolute_url)

            jobs.append(
                JobCreate(
                    title=text,
                    company=self._source_name,
                    url=absolute_url,
                    source=self._source_name,
                )
            )
            added += 1

        return added

    async def scrape(self) -> list[JobCreate]:
        await self.polite_goto(self._build_url())

        seen_urls: set[str] = set()
        jobs: list[JobCreate] = []
        stale_pages = 0

        for _ in range(_MAX_PAGES):
            await self._wait_for_page_settle()
            await self._detect_antibot_block()
            added = await self._collect_jobs_from_current_page(seen_urls, jobs)

            if added == 0:
                stale_pages += 1
            else:
                stale_pages = 0

            next_item = self.page.locator(
                "ul.pagination li.page-item", has_text="Next"
            ).first
            if await next_item.count() == 0:
                break

            classes = ((await next_item.get_attribute("class")) or "").lower()
            if "disabled" in classes:
                break

            next_link = next_item.locator("a.page-link").first
            if await next_link.count() == 0:
                break

            active_before = await self._active_page_token()
            await next_link.click()
            await self._wait_for_page_settle()
            active_after = await self._active_page_token()

            if active_before and active_after and active_before == active_after:
                stale_pages += 1

            if stale_pages >= _MAX_STALE_PAGES:
                break

        return jobs
