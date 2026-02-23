import threading
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Response
from fastapi.responses import PlainTextResponse

from config import LOG_FILE
from imap_listener import listener_loop


@asynccontextmanager
async def lifespan(_: FastAPI):
    stop_event = threading.Event()
    listener_thread = threading.Thread(target=listener_loop, args=(stop_event,), daemon=True)
    listener_thread.start()

    yield

    stop_event.set()
    if listener_thread.is_alive():
        listener_thread.join(timeout=5)


app = FastAPI(title="Status Page Log API", lifespan=lifespan)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "Push-based Status Tracker"}


@app.head("/health")
def health_head() -> Response:
    return Response(status_code=200)


@app.get("/")
def get_logs() -> PlainTextResponse:
    if not LOG_FILE.exists():
        return PlainTextResponse("No incidents logged yet.")
    return PlainTextResponse(LOG_FILE.read_text(encoding="utf-8"))


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=False)
