FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install uv binary from the official image.
COPY --from=ghcr.io/astral-sh/uv:0.10.4 /uv /uvx /bin/

# Use the project virtualenv by default.
ENV PATH="/app/.venv/bin:$PATH"
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PYTHONPATH=/app

# Install dependencies first for better layer caching.
COPY pyproject.toml uv.lock README.md /app/
RUN uv sync --frozen --no-install-project

# Copy source code.
COPY . /app

# Ensure runtime environment is fully synced to lockfile.
RUN uv sync --frozen

# Render expects web services to bind to PORT (defaults to 10000).
# Use a single worker so the IMAP listener is started only once.
CMD ["sh", "-c", "uv run uvicorn api:app --host 0.0.0.0 --port ${PORT:-10000} --workers 1"]
