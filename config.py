import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

IMAP_HOST: str = os.getenv("IMAP_HOST", "imap.gmail.com")
EMAIL_USER: str | None = os.getenv("EMAIL_USER")
EMAIL_PASS: str | None = os.getenv("EMAIL_PASS")

LOG_FILE: Path = Path("incident_updates.log")

# optional sender allowlist, if its empty, all incoming messages are processed
# NOTE: you must individually subscribe to email updates from each service for example https://status.onesignal.com/ https://status.openai.com/ etc
TRACKED_SENDERS: set[str] = {
    "no-reply@status.incident.io", # Incident.io status
    "noreply@statuspage.io" # Atlassian status
}
TRACKED_SENDERS = {sender.lower() for sender in TRACKED_SENDERS}
