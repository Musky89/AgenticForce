import asyncio
import json
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)


class EventBus:
    """In-memory asyncio.Queue-based pub/sub for SSE streaming."""

    def __init__(self):
        self._subscribers: dict[str, list[asyncio.Queue]] = defaultdict(list)

    def subscribe(self, project_id: str) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue()
        self._subscribers[project_id].append(queue)
        logger.info(f"SSE subscriber added for project {project_id} (total: {len(self._subscribers[project_id])})")
        return queue

    def unsubscribe(self, project_id: str, queue: asyncio.Queue):
        if project_id in self._subscribers:
            self._subscribers[project_id] = [q for q in self._subscribers[project_id] if q is not queue]
            if not self._subscribers[project_id]:
                del self._subscribers[project_id]
        logger.info(f"SSE subscriber removed for project {project_id}")

    async def publish(self, project_id: str, event: dict):
        queues = self._subscribers.get(project_id, [])
        for queue in queues:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                logger.warning(f"SSE queue full for project {project_id}, dropping event")

    async def publish_task_started(self, project_id: str, task_id: str, agent_role: str):
        await self.publish(project_id, {
            "type": "task_started",
            "task_id": task_id,
            "agent_role": agent_role,
        })

    async def publish_task_completed(self, project_id: str, task_id: str, output_preview: str = ""):
        await self.publish(project_id, {
            "type": "task_completed",
            "task_id": task_id,
            "output_preview": output_preview[:500],
        })

    async def publish_image_generated(self, project_id: str, image_id: str, label: str = ""):
        await self.publish(project_id, {
            "type": "image_generated",
            "image_id": image_id,
            "label": label,
        })

    async def publish_quality_scored(self, project_id: str, image_id: str, score: float):
        await self.publish(project_id, {
            "type": "quality_scored",
            "image_id": image_id,
            "score": score,
        })

    def format_sse(self, event: dict) -> str:
        data = json.dumps(event)
        return f"data: {data}\n\n"


event_bus = EventBus()
