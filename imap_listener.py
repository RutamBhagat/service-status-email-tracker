import time
import threading
from datetime import datetime, timedelta, timezone

from imapclient import IMAPClient

from config import EMAIL_PASS, EMAIL_USER, IMAP_HOST, LOG_FILE, LOOKBACK_SECONDS, TRACKED_SENDERS
from email_processing import process_email


def listener_loop(stop_event: threading.Event) -> None:
    if not EMAIL_USER or not EMAIL_PASS:
        print("ERROR: Missing credentials. Set EMAIL_USER and EMAIL_PASS.")
        return

    processed_uids: set[int] = set()

    while not stop_event.is_set():
        print(f"Connecting to {IMAP_HOST}...")
        try:
            with IMAPClient(IMAP_HOST) as server:
                server.login(EMAIL_USER, EMAIL_PASS)
                server.select_folder("INBOX")
                print("Connected! Listening for real-time push events via IMAP IDLE...")

                server.idle()
                while not stop_event.is_set():
                    responses = server.idle_check(timeout=30) # IDLE push + periodic check window
                    if not responses:
                        continue

                    server.idle_done()
                    window_start = datetime.now(timezone.utc) - timedelta(seconds=LOOKBACK_SECONDS)
                    messages = server.search(["SINCE", window_start.date()])
                    if messages:
                        fetched = server.fetch(messages, ["RFC822", "INTERNALDATE"])
                        for uid, msg_data in fetched.items():
                            if uid in processed_uids:
                                continue

                            internal_date = msg_data.get(b"INTERNALDATE")
                            if internal_date is not None:
                                if internal_date.tzinfo is None:
                                    internal_date = internal_date.replace(tzinfo=timezone.utc)
                                else:
                                    internal_date = internal_date.astimezone(timezone.utc)
                                if internal_date < window_start:
                                    continue

                            process_email(
                                message_data=msg_data,
                                tracked_senders=TRACKED_SENDERS,
                                log_file=LOG_FILE,
                            )
                            processed_uids.add(uid)
                    server.idle()

                try:
                    server.idle_done()
                except Exception:
                    pass
        except Exception as error:
            print(f"IMAP Connection error: {error}")
            if not stop_event.is_set():
                time.sleep(5)
