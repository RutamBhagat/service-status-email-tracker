import email
import re
from email.policy import default
from email.utils import parseaddr
from pathlib import Path

from incident_logger import write_and_print_log


def extract_email_body(msg: email.message.EmailMessage) -> str:
    body_part = msg.get_body(preferencelist=("plain", "html"))
    if body_part is not None:
        content = body_part.get_content()
        return str(content).replace("\r", "").strip()

    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() != "text/plain":
                continue
            if part.get_content_disposition() == "attachment":
                continue
            content = part.get_content()
            return str(content).replace("\r", "").strip()

    content = msg.get_content()
    return str(content).replace("\r", "").strip()


def extract_statuspage_fields(subject: str, body: str) -> tuple[str | None, str | None]:
    lines = [line.strip() for line in body.splitlines()]
    non_empty_lines = [line for line in lines if line]

    product: str | None = None
    status: str | None = None
    incident_title = non_empty_lines[0] if non_empty_lines else None

    for index, line in enumerate(lines):
        if line.lower() not in {"components affected", "affected components"}:
            continue
        for next_line in lines[index + 1:]:
            if next_line:
                product = next_line
                break
        break

    for index, line in enumerate(lines):
        match = re.match(r"(?i)^(new incident|incident status|status)\s*:\s*(.+)$", line)
        if not match:
            continue

        event_state = match.group(2).strip()
        event_message = ""
        for next_line in lines[index + 1:]:
            if not next_line:
                continue
            if next_line.lower() in {"time posted", "components affected", "affected components"}:
                break
            if re.match(r"(?i)^(new incident|incident status|status)\s*:", next_line):
                break
            event_message = next_line
            break

        status = f"{event_state} - {event_message}" if event_message else event_state
        break

    if product is None and incident_title:
        product = incident_title

    if status is None and incident_title:
        status = incident_title

    if status is None:
        trimmed_subject = subject.strip()
        status = trimmed_subject or None

    return product, status


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

    body = extract_email_body(msg)
    parsed_product, parsed_status = extract_statuspage_fields(subject=subject, body=body)

    product = parsed_product or sender_name or sender_email or "Unknown Sender"
    status = parsed_status or subject

    write_and_print_log(log_file=log_file, product=product, status=status, body=body)
