import time
from pathlib import Path


def build_log_entry(timestamp: str, product: str, status: str) -> str:
    return (
        f"[{timestamp}] Product: {product}\n"
        f"Status: {status}\n"
        f"{'-' * 60}\n"
    )


def write_and_print_log(log_file: Path, product: str, status: str) -> None:
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_entry = build_log_entry(timestamp, product, status)

    print(log_entry, end="")
    with log_file.open("a", encoding="utf-8") as file:
        file.write(log_entry)
