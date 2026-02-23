# Repository Guidelines

## Project Structure & Module Organization
This repository is a small FastAPI service that listens for IMAP status emails and appends incidents to a log file.

- `api.py`: FastAPI app, health endpoints, and listener thread lifecycle.
- `imap_listener.py`: IMAP IDLE loop and reconnect behavior.
- `email_processing.py`: Parses inbound emails and filters allowed senders.
- `incident_logger.py`: Builds and writes incident log entries.
- `config.py`: Environment-driven settings (`EMAIL_USER`, `EMAIL_PASS`, `IMAP_HOST`, sender allowlist).
- `incident_updates.log`: Runtime output log (generated/updated at runtime).
- `Dockerfile`, `render.yaml`: Container and Render deployment config.

## Build and Development Commands
- `uv sync`: Install dependencies from `pyproject.toml`/`uv.lock`.
- `uv run uvicorn api:app --host 0.0.0.0 --port 8000 --workers 1`: Run locally with one worker (important so the IMAP listener starts once).
- `uv run python api.py`: Alternate local run path using the module entrypoint.
- `docker build -t service-status-email-tracker .`: Build production container image.
- `docker run --env-file .env -p 10000:10000 service-status-email-tracker`: Run containerized service locally.
