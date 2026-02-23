# bolena-simplified

IMAP IDLE listener that receives status emails in real time and prints incident status to stdout.

## Run with uv

1. Create and sync environment:

```bash
uv sync
```

2. Set environment variables (example):

```bash
cp .env.example .env
export $(grep -v '^#' .env | xargs)
```

3. Run:

```bash
uv run python bolena.py
```

Sender filtering is configured in `bolena.py` via the `EXPECTED_SENDERS` array.
Add one entry per incident sender email address you want to monitor.
Incident logs are appended to `incident_updates.log` in the project directory.

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
ExecStart=/usr/bin/env uv run python bolena.py
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
