import asyncio

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app.services.event_bus import event_bus

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/stream")
async def event_stream(project_id: str, request: Request):
    """SSE endpoint for realtime agent status updates."""
    queue = event_bus.subscribe(project_id)

    async def generate():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield event_bus.format_sse(event)
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        finally:
            event_bus.unsubscribe(project_id, queue)

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
