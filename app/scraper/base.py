"""Abstract base class for all Playwright-based scrapers."""

import asyncio
from abc import ABC, abstractmethod

from playwright.async_api import Browser, BrowserContext, Page, async_playwright

from app.config import settings
from app.schemas import JobCreate


class BaseScraper(ABC):
    """
    Base class for all job scrapers.

    Subclass this and implement `scrape()` to build a new scraper.
    Each scraper gets its own Playwright browser context (isolated cookies/state).

    Example:
        class LinkedInScraper(BaseScraper):
            source = "linkedin"

            async def scrape(self) -> list[JobCreate]:
                await self.page.goto("https://www.linkedin.com/jobs/...")
                # ... parse DOM, yield JobCreate instances ...
                return jobs
    """

    source: str  # Must be set on subclasses

    def __init__(self) -> None:
        self._playwright = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    @property
    def page(self) -> Page:
        if self._page is None:
            raise RuntimeError(
                "Scraper not started. Use `async with scraper:` context manager."
            )
        return self._page

    async def __aenter__(self) -> "BaseScraper":
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=settings.playwright_headless,
        )
        self._context = await self._browser.new_context(
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 900},
        )
        self._page = await self._context.new_page()
        self._page.set_default_timeout(settings.scraper_timeout_seconds * 1000)
        return self

    async def __aexit__(self, *args: object) -> None:
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

    async def polite_goto(self, url: str) -> None:
        """Navigate to a URL with a configurable delay to respect rate limits."""
        await asyncio.sleep(settings.scraper_delay_seconds)
        await self.page.goto(url, wait_until="domcontentloaded")

    @abstractmethod
    async def scrape(self) -> list[JobCreate]:
        """
        Perform the scraping. Must be implemented by subclasses.

        Returns a list of JobCreate schemas ready to be inserted into the DB.
        """
        ...
