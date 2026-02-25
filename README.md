# req-hunter

A Python-based job listing scraper for tracking and aggregating open roles across multiple sources.

## Stack

- **Scraper** — [Playwright](https://playwright.dev/python/) (Chromium, headless) + [httpx](https://www.python-httpx.org/) for Workday ATS
- **API** — [FastAPI](https://fastapi.tiangolo.com/) + [Uvicorn](https://www.uvicorn.org/)
- **Database** — PostgreSQL 16 via async [SQLAlchemy](https://docs.sqlalchemy.org/) + [asyncpg](https://github.com/MagicStack/asyncpg)
- **Migrations** — [Alembic](https://alembic.sqlalchemy.org/)
- **Dev environment** — VS Code Dev Container (Docker Compose)

## Getting started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [VS Code](https://code.visualstudio.com/) with the [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)

### Open in dev container

1. Open this repo in VS Code
2. When prompted, click **Reopen in Container** (or `Cmd+Shift+P` → "Dev Containers: Reopen in Container")
3. The first build takes a few minutes — it installs Python deps and Playwright's Chromium browser

### First-time setup

Once inside the container terminal:

```bash
# Copy the example env file (edit SECRET_KEY at minimum)
cp .env.example .env

# Apply the initial DB migration
export $(grep -v '^#' .env | xargs)
alembic upgrade head

# Start the API server with hot reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`, the web UI at `http://localhost:8000/ui/`, and interactive docs at `http://localhost:8000/docs`.

---

## How to use

### 1. Add a source

A source is a website you want to scrape and the keyword to search for (e.g. a job title).

```bash
curl -X POST http://localhost:8000/api/v1/sources/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corp",
    "base_url": "https://acme.wd5.myworkdayjobs.com/en-US/External",
    "keyword": "software engineer"
  }'
```

For non-Workday job boards you can also specify which query parameter the site uses for search (defaults to `q`):

```bash
curl -X POST http://localhost:8000/api/v1/sources/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Example Corp",
    "base_url": "https://example.com/careers",
    "keyword": "data engineer",
    "query_param": "search"
  }'
```

**Workday sites** (`myworkdayjobs.com`) are detected automatically and scraped via Workday's internal API — no browser needed, and full pagination is supported. All other sites are scraped with a headless Chromium browser.

### 2. Run a scrape

Scrape all active sources at once:

```bash
curl -X POST http://localhost:8000/api/v1/scrape/run
```

Or scrape a single source by its ID:

```bash
curl -X POST http://localhost:8000/api/v1/scrape/run/1
```

The response tells you how many jobs were found and how many were new:

```json
{
  "sources_processed": 2,
  "jobs_found": 34,
  "jobs_new": 5,
  "errors": []
}
```

Jobs are deduplicated by URL — re-running a scrape won't reset statuses you've already set.

### 3. Browse results

```bash
# All new jobs
curl "http://localhost:8000/api/v1/jobs/?status=new"

# With pagination
curl "http://localhost:8000/api/v1/jobs/?limit=20&offset=0"
```

### 4. Update a job's status

```bash
curl -X PATCH http://localhost:8000/api/v1/jobs/42 \
  -H "Content-Type: application/json" \
  -d '{"status": "applied"}'
```

### Job statuses

`new` → `seen` → `applied` / `rejected` / `ignored`

### Managing sources

```bash
# List all sources
curl http://localhost:8000/api/v1/sources/

# Pause a source (stop it from being scraped)
curl -X PATCH http://localhost:8000/api/v1/sources/1 \
  -H "Content-Type: application/json" \
  -d '{"is_active": false}'

# Update the keyword
curl -X PATCH http://localhost:8000/api/v1/sources/1 \
  -H "Content-Type: application/json" \
  -d '{"keyword": "senior software engineer"}'

# Restrict matching URLs to a path fragment
curl -X PATCH http://localhost:8000/api/v1/sources/1 \
  -H "Content-Type: application/json" \
  -d '{"url_path_filter": "/jobs/"}'

# Clear a blocked source and reactivate it
curl -X PATCH http://localhost:8000/api/v1/sources/1 \
  -H "Content-Type: application/json" \
  -d '{"clear_blocked": true}'

# Delete a source
curl -X DELETE http://localhost:8000/api/v1/sources/1
```

### 5. View logs and scheduler state

```bash
# Tail recent application logs
curl "http://localhost:8000/api/v1/logs/?limit=200"

# Get the current scrape schedule
curl "http://localhost:8000/api/v1/schedule/"

# Enable automatic scraping every 60 minutes
curl -X PATCH http://localhost:8000/api/v1/schedule/ \
  -H "Content-Type: application/json" \
  -d '{"is_enabled": true, "interval_minutes": 60}'
```

`interval_minutes` is normalized to a minimum of `5`.

---

## API reference

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Liveness check |
| `/` | GET | Redirect to web UI (`/ui/`) |
| `/ui/` | GET | Web UI |
| `/api/v1/sources/` | GET | List all sources |
| `/api/v1/sources/` | POST | Add a new source |
| `/api/v1/sources/{id}` | GET | Get a source by ID |
| `/api/v1/sources/{id}` | PATCH | Update a source |
| `/api/v1/sources/{id}` | DELETE | Delete a source |
| `/api/v1/scrape/run` | POST | Scrape all active sources |
| `/api/v1/scrape/run/{id}` | POST | Scrape one source by ID |
| `/api/v1/logs/` | GET | Read recent app logs (`?limit=`) |
| `/api/v1/schedule/` | GET | Read automatic scrape schedule |
| `/api/v1/schedule/` | PATCH | Update schedule (`is_enabled`, `interval_minutes`) |
| `/api/v1/jobs/` | GET | List jobs (`?status=`, `?limit=`, `?offset=`) |
| `/api/v1/jobs/{id}` | GET | Get a job by ID |
| `/api/v1/jobs/{id}` | PATCH | Update a job's status |
| `/docs` | GET | Swagger UI |
| `/redoc` | GET | ReDoc |

---

## Project structure

```
app/
├── main.py           # FastAPI app factory
├── config.py         # Settings loaded from .env
├── database.py       # Async SQLAlchemy engine and session
├── models.py         # Job, Source, and ScrapeSchedule ORM models
├── schemas.py        # Pydantic request/response schemas
├── scheduler.py      # Background scheduler for recurring scrape runs
├── logging_utils.py  # Logging config and tail helpers
├── routers/
│   ├── jobs.py       # Job listing endpoints
│   ├── sources.py    # Source management endpoints
│   ├── scrape.py     # Scrape trigger endpoints
│   ├── logs.py       # Log reading endpoints
│   └── schedule.py   # Scheduler config endpoints
├── static/           # Web UI assets served at /ui/
└── scraper/
    ├── base.py       # Abstract BaseScraper (Playwright)
    ├── generic.py    # Heuristic scraper for arbitrary job boards
    ├── workday.py    # Workday ATS API scraper
    └── runner.py     # Dispatcher — routes sources to the right scraper
alembic/              # Database migrations
.devcontainer/        # VS Code dev container config
```

## Adding a custom scraper

For sites where the generic heuristic doesn't work well, subclass `BaseScraper` and implement `scrape()`:

```python
from app.scraper.base import BaseScraper
from app.schemas import JobCreate

class AcmeScraper(BaseScraper):
    source = "acme"

    async def scrape(self) -> list[JobCreate]:
        await self.polite_goto("https://acme.com/jobs?q=engineer")
        # use self.page (Playwright Page) to extract listings
        return []
```

Then register it in `app/scraper/runner.py`'s `_build_scraper()` function.

`polite_goto()` adds a configurable delay between requests (`SCRAPER_DELAY_SECONDS` in `.env`).

## Database migrations

```bash
# Alembic requires env vars to be exported in the shell
export $(grep -v '^#' .env | xargs)

# After changing models.py, generate a new migration
alembic revision --autogenerate -m "description of change"

# Apply all pending migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1
```

## Environment variables

See [.env.example](.env.example) for all available options. Key variables:

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | — | Async PostgreSQL URL (used by the app) |
| `DATABASE_SYNC_URL` | — | Sync PostgreSQL URL (used by Alembic) |
| `APP_ENV` | `development` | Environment name |
| `APP_DEBUG` | `true` | Enables FastAPI debug mode and permissive CORS |
| `APP_HOST` | `0.0.0.0` | App host setting |
| `APP_PORT` | `8000` | App port setting |
| `SECRET_KEY` | — | App secret value |
| `PLAYWRIGHT_HEADLESS` | `true` | Run browser headlessly |
| `SCRAPER_DELAY_SECONDS` | `2` | Delay between requests / pagination |
| `SCRAPER_TIMEOUT_SECONDS` | `30` | Per-request timeout |
| `LOG_FILE_PATH` | `logs/req-hunter.log` | Log file path |
| `LOG_LEVEL` | `INFO` | Root logging level |
| `LOG_MAX_BYTES` | `1048576` | Log rotation max file size in bytes |
| `LOG_BACKUP_COUNT` | `3` | Number of rotated log files to keep |
