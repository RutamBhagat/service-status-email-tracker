import email
from email.policy import default
from email.utils import parseaddr
from pathlib import Path

from incident_logger import write_and_print_log


def process_email(
    message_data: dict[bytes, bytes],
    tracked_senders: set[str],
    log_file: Path,
) -> None:
    raw_email = message_data[b"RFC822"]
    msg = email.message_from_bytes(raw_email, policy=default)

    subject = (msg.get("subject") or "No Subject").replace("\r", "").replace("\n", "")
    raw_from = msg.get("from", "Unknown Sender")
    sender_name, sender_email = parseaddr(raw_from)
    sender_email = sender_email.lower()

    if tracked_senders and sender_email not in tracked_senders:
        return

    product = sender_name or sender_email or "Unknown Sender"
    write_and_print_log(log_file=log_file, product=product, status=subject)
