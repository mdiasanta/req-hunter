# req-hunter

A Python-based job listing scraper for tracking and aggregating open roles across multiple sources.

## Stack

- **Scraper** — [Playwright](https://playwright.dev/python/) (Chromium, headless)
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

# Generate and apply the initial DB migration
alembic revision --autogenerate -m "create jobs table"
alembic upgrade head

# Start the API server with hot reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`.

## API

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Liveness check |
| `/api/v1/jobs/` | GET | List jobs (supports `?status=`, `?limit=`, `?offset=`) |
| `/api/v1/jobs/{id}` | GET | Get a single job by ID |
| `/api/v1/jobs/{id}` | PATCH | Update a job's status |
| `/docs` | GET | Swagger UI |
| `/redoc` | GET | ReDoc |

### Job statuses

`new` → `seen` → `applied` / `rejected` / `ignored`

## Project structure

```
app/
├── main.py           # FastAPI app factory
├── config.py         # Settings loaded from .env
├── database.py       # Async SQLAlchemy engine and session
├── models.py         # Job ORM model
├── schemas.py        # Pydantic request/response schemas
├── routers/
│   └── jobs.py       # Job listing endpoints
└── scraper/
    └── base.py       # Abstract BaseScraper (extend this to add sources)
alembic/              # Database migrations
.devcontainer/        # VS Code dev container config
```

## Adding a scraper

Subclass `BaseScraper` in `app/scraper/` and implement the `scrape()` method:

```python
from app.scraper.base import BaseScraper
from app.schemas import JobCreate

class ExampleScraper(BaseScraper):
    source = "example"

    async def scrape(self) -> list[JobCreate]:
        await self.polite_goto("https://example.com/jobs")
        # parse self.page and return a list of JobCreate
        return []
```

`polite_goto()` adds a configurable delay between requests (`SCRAPER_DELAY_SECONDS` in `.env`).

## Database migrations

```bash
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
| `PLAYWRIGHT_HEADLESS` | `true` | Run browser headlessly |
| `SCRAPER_DELAY_SECONDS` | `2` | Delay between scraper requests |
