import time
import email
import os
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from email.policy import default
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import PlainTextResponse
from imapclient import IMAPClient

load_dotenv()

IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")

EXPECTED_SENDERS = [
    "no-reply@status.incident.io",
    "rutambhagat@gmail.com"
]
LOG_FILE_PATH = "incident_updates.log"
LOG_FILE = Path(LOG_FILE_PATH)


@asynccontextmanager
async def lifespan(app: FastAPI):
    stop_event = threading.Event()
    listener_thread = threading.Thread(target=listener_loop, args=(stop_event,), daemon=True)
    app.state.listener_stop_event = stop_event
    app.state.listener_thread = listener_thread
    listener_thread.start()
    try:
        yield
    finally:
        stop_event.set()
        if listener_thread.is_alive():
            listener_thread.join(timeout=15)


app = FastAPI(title="Bolena Incident Log API", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.head("/health")
def health_head() -> Response:
    return Response(status_code=200)


@app.get("/logs")
def get_logs() -> PlainTextResponse:
    if not LOG_FILE.exists():
        raise HTTPException(status_code=404, detail="Log file not found")
    return PlainTextResponse(LOG_FILE.read_text(encoding="utf-8"))


def format_log_entry(timestamp, product, status):
    """Builds a log line close to the assignment example format."""
    return (
        f"[{timestamp}] Product: {product}\n"
        f"Status: {status}\n"
    )


def process_email(message_data):
    """Parses the pushed email and extracts incident info."""
    raw_email = message_data[b'RFC822']
    msg = email.message_from_bytes(raw_email, policy=default)

    subject = (msg.get("subject") or "").replace('\r', '').replace('\n', '')
    sender = (msg.get("from") or "Unknown Sender").replace('\r', '').replace('\n', '')
    product = f"({sender})"

    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    log_entry = format_log_entry(timestamp, product, subject)

    print(log_entry, end="")
    print("-" * 60)

    with open(LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
        log_file.write(log_entry)


def listener_loop(stop_event: threading.Event):
    if not EMAIL_USER or not EMAIL_PASS:
        print("Missing credentials. Set EMAIL_USER and EMAIL_PASS environment variables.")
        return

    while not stop_event.is_set():
        print(f"Connecting to {IMAP_HOST}...")
        try:
            with IMAPClient(IMAP_HOST) as server:
                server.login(EMAIL_USER, EMAIL_PASS)
                server.select_folder('INBOX')
                print("Connected! Listening for real-time push events via IMAP IDLE...")
                server.idle()

                while not stop_event.is_set():
                    responses = server.idle_check(timeout=10)
                    if responses:
                        server.idle_done()
                        messages = set()
                        for sender in EXPECTED_SENDERS:
                            matches = server.search(['UNSEEN', 'FROM', sender])
                            messages.update(matches)

                        if messages:
                            for uid, msg_data in server.fetch(sorted(messages), 'RFC822').items():
                                process_email(msg_data)
                        server.idle()

                try:
                    server.idle_done()
                except Exception:
                    pass
        except Exception as e:
            print(f"Connection error: {e}")
            if not stop_event.is_set():
                time.sleep(5)

def run_api():
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    run_api()
