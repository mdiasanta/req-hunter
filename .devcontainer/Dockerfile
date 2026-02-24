FROM mcr.microsoft.com/devcontainers/python:3.0.5-3.12-bookworm

# Install OS-level dependencies needed by Playwright's Chromium + psql CLI
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libxkbcommon0 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    postgresql-client \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency manifest first to leverage Docker layer caching.
# This layer is only invalidated when pyproject.toml changes.
COPY pyproject.toml /tmp/req-hunter-deps/pyproject.toml
RUN mkdir -p /tmp/req-hunter-deps/app \
    && touch /tmp/req-hunter-deps/app/__init__.py \
    && touch /tmp/req-hunter-deps/README.md

# Install all Python dependencies (not the project itself in editable mode —
# that happens via postCreateCommand against the live volume mount)
RUN pip install --no-cache-dir /tmp/req-hunter-deps[dev] \
    && rm -rf /tmp/req-hunter-deps

# Bake Playwright Chromium into the image to avoid re-downloading on every rebuild.
# postCreateCommand re-runs this but it becomes a fast no-op if the version matches.
RUN playwright install --with-deps chromium

# Ensure the vscode user owns the Playwright browser cache directory
RUN mkdir -p /home/vscode/.cache/ms-playwright \
    && chown -R vscode:vscode /home/vscode/.cache

USER vscode
