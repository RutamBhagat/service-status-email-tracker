import time
import email
import os
from email.policy import default
from imapclient import IMAPClient

# --- Configuration ---
IMAP_HOST = os.getenv("IMAP_HOST", "imap.gmail.com")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EXPECTED_SENDERS = [
    "no-reply@status.incident.io",
]

def process_email(message_data):
    """Parses the pushed email and extracts incident info."""
    raw_email = message_data[b'RFC822']
    msg = email.message_from_bytes(raw_email, policy=default)

    subject = (msg.get("subject") or "").replace('\r', '').replace('\n', '')
    sender = (msg.get("from") or "Unknown Sender").replace('\r', '').replace('\n', '')

    # Simple console output satisfying the requirement
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] Sender: {sender}")
    print(f"Status: {subject}")
    print("-" * 60)

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

if __name__ == "__main__":
    main()
