# bolena-simplified

IMAP IDLE listener that receives status emails in real time and prints incident status to stdout.

The implementation is modularized for readability:
- `config.py`: environment + app configuration
- `email_processing.py`: RFC822 parsing + sender filtering
- `incident_logger.py`: log formatting + append/print
- `imap_listener.py`: push-based IMAP IDLE loop
- `api.py`: FastAPI app + lifespan thread lifecycle

## Run with uv

1. Create and sync environment:

```bash
uv sync
```

2. Create `.env` (example):

```bash
cp .env.example .env
```

`config.py` auto-loads `.env` using `python-dotenv`.

3. Run:

```bash
uv run python api.py
```

Sender filtering is configured in `config.py` via the `TRACKED_SENDERS` set.
Add one entry per incident sender email address you want to monitor.
Incident logs are appended to `incident_updates.log` in the project directory.

API endpoints are served from `api.py`:

```bash
uv run python api.py
```

- `GET /health`
- `HEAD /health`
- `GET /`

The same process runs both:
- IMAP listener (started on FastAPI startup, stopped on shutdown)
- FastAPI server on `0.0.0.0:8000`

## Deploy (VM + systemd)

This app is a long-running worker, so deploy it as a service on a VM.

1. Copy project to server and run:

```bash
cd /opt/bolena-simplified
uv sync --frozen
```

2. Create env file:

```bash
sudo tee /etc/bolena.env >/dev/null <<'EOF'
IMAP_HOST=imap.gmail.com
EMAIL_USER=your.status.tracker@gmail.com
EMAIL_PASS=your_app_specific_password
EOF
```

3. Create systemd unit:

```bash
sudo tee /etc/systemd/system/bolena.service >/dev/null <<'EOF'
[Unit]
Description=Bolena IMAP status listener
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/opt/bolena-simplified
EnvironmentFile=/etc/bolena.env
ExecStart=/usr/bin/env uv run python api.py
Restart=always
RestartSec=5
User=ubuntu
Group=ubuntu

[Install]
WantedBy=multi-user.target
EOF
```

4. Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now bolena.service
sudo systemctl status bolena.service
```

5. View logs:

```bash
journalctl -u bolena.service -f
```
