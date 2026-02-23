import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

IMAP_HOST: str = os.getenv("IMAP_HOST", "imap.gmail.com")
EMAIL_USER: str | None = os.getenv("EMAIL_USER")
EMAIL_PASS: str | None = os.getenv("EMAIL_PASS")

LOG_FILE: Path = Path("incident_updates.log")

# Optional sender allowlist. If empty, all incoming messages are processed.
TRACKED_SENDERS: set[str] = {
    "no-reply@status.incident.io",
    "rutambhagat@gmail.com",
}
TRACKED_SENDERS = {sender.lower() for sender in TRACKED_SENDERS}
