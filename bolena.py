import time
import email
import os
from pathlib import Path
from email.policy import default
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import FileResponse
from imapclient import IMAPClient

# --- Configuration ---
IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
RUN_MODE = os.getenv("RUN_MODE", "listener").strip().lower()
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
EXPECTED_SENDERS = [
    "no-reply@status.incident.io",
]
LOG_FILE_PATH = "incident_updates.log"
LOG_FILE = Path(LOG_FILE_PATH)

app = FastAPI(title="Bolena Incident Log API")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.head("/health")
def health_head() -> Response:
    return Response(status_code=200)


@app.get("/logs")
def get_logs() -> FileResponse:
    if not LOG_FILE.exists():
        raise HTTPException(status_code=404, detail="Log file not found")
    return FileResponse(LOG_FILE, media_type="text/plain", filename=LOG_FILE.name)


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
    product = f"OpenAI API ({sender})"

    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    log_entry = format_log_entry(timestamp, product, subject)

    # Console output
    print(log_entry, end="")
    print("-" * 60)

    # Persist in local log file
    with open(LOG_FILE_PATH, "a", encoding="utf-8") as log_file:
        log_file.write(log_entry)

def main():
    if not EMAIL_USER or not EMAIL_PASS:
        raise ValueError(
            "Missing credentials. Set EMAIL_USER and EMAIL_PASS environment variables."
        )

    print(f"Connecting to {IMAP_HOST}...")
    try:
        with IMAPClient(IMAP_HOST) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.select_folder('INBOX')
            print("Connected! Listening for real-time push events via IMAP IDLE...")
            
            # Enter IDLE mode (Strict Push Architecture - No polling!)
            server.idle()
            
            while True:
                # The script blocks here. It consumes virtually 0 CPU/Bandwidth.
                # It will wake up the millisecond the server PUSHES a new email event.
                responses = server.idle_check(timeout=600)
                
                if responses:
                    # Temporarily pause IDLE to interact with the inbox
                    server.idle_done() 

                    # Fetch unread emails only from configured incident senders.
                    messages = set()
                    for sender in EXPECTED_SENDERS:
                        matches = server.search(['UNSEEN', 'FROM', sender])
                        messages.update(matches)

                    if messages:
                        for uid, msg_data in server.fetch(sorted(messages), 'RFC822').items():
                            process_email(msg_data)
                    
                    # Resume IDLE mode
                    server.idle() 
                    
    except KeyboardInterrupt:
        print("\nExiting Event Listener...")
    except Exception as e:
        print(f"Connection error: {e}")


def run_api():
    import uvicorn

    uvicorn.run(app, host=API_HOST, port=API_PORT)


if __name__ == "__main__":
    if RUN_MODE == "api":
        run_api()
    else:
        main()
