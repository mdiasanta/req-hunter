"""Generic Playwright-based scraper for arbitrary job boards.

Navigates to `{base_url}?{query_param}={keyword}`, waits for the page to
settle, then extracts links whose URLs look like individual job postings.

This works well for simple job boards (custom career pages, Lever, Greenhouse,
etc.). For Workday ATS sites use WorkdayScraper instead.
"""

from urllib.parse import quote_plus, urljoin

from app.schemas import JobCreate
from app.scraper.base import BaseScraper

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


class GenericScraper(BaseScraper):
    """Heuristic scraper that extracts job links from an arbitrary job board page."""

    def __init__(
        self,
        source_name: str,
        base_url: str,
        keyword: str,
        query_param: str = "q",
    ) -> None:
        super().__init__()
        self.source = source_name
        self._source_name = source_name
        self._base_url = base_url
        self._keyword = keyword
        self._query_param = query_param

    def _build_url(self) -> str:
        sep = "&" if "?" in self._base_url else "?"
        return f"{self._base_url}{sep}{self._query_param}={quote_plus(self._keyword)}"

    @staticmethod
    def _looks_like_job_url(href: str) -> bool:
        href_lower = href.lower()
        return any(frag in href_lower for frag in _JOB_URL_FRAGMENTS)

    async def scrape(self) -> list[JobCreate]:
        await self.polite_goto(self._build_url())

        # Give SPAs a chance to finish rendering before we walk the DOM
        try:
            await self.page.wait_for_load_state("networkidle", timeout=10_000)
        except Exception:
            pass  # Proceed with whatever is rendered

        page_url = self.page.url
        links = await self.page.locator("a[href]").all()

        seen_urls: set[str] = set()
        jobs: list[JobCreate] = []

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

        return jobs
