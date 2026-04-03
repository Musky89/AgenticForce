"""Typed inter-agent communication protocol.

Provides structured message passing between agents with persistence
and helper factories for common message types.
"""
import uuid
import logging
from datetime import datetime
from enum import Enum

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import MessageLog

logger = logging.getLogger(__name__)


class MessageType(str, Enum):
    BRIEF = "brief"
    HANDOFF = "handoff"
    ESCALATION = "escalation"
    FEEDBACK = "feedback"
    STATUS = "status"


class AgentMessage(BaseModel):
    id: str
    type: MessageType
    from_agent: str
    to_agent: str | None = None
    project_id: str
    timestamp: datetime

    # BRIEF fields
    objective: str | None = None
    context: dict | None = None
    constraints: list[str] | None = None
    expected_deliverables: list[str] | None = None

    # HANDOFF fields
    summary: str | None = None
    artifacts: list[dict] | None = None
    notes: str | None = None

    # ESCALATION fields
    question: str | None = None
    options: list[str] | None = None
    impact: str | None = None

    # FEEDBACK fields
    score: float | None = None
    comments: list[dict] | None = None

    # STATUS fields
    status: str | None = None
    progress_pct: int | None = None
    current_task: str | None = None


async def send_message(db: AsyncSession, message: AgentMessage) -> MessageLog:
    """Persist an agent message and return the log entry."""
    log = MessageLog(
        id=message.id,
        project_id=message.project_id,
        message_type=message.type.value,
        from_agent=message.from_agent,
        to_agent=message.to_agent,
        payload=message.model_dump(mode="json"),
    )
    db.add(log)
    await db.flush()
    logger.info(
        "Agent message %s: %s -> %s [%s]",
        message.type.value, message.from_agent,
        message.to_agent or "broadcast", message.project_id,
    )
    return log


async def get_messages(
    db: AsyncSession,
    project_id: str,
    type: MessageType | None = None,
) -> list[MessageLog]:
    """Retrieve messages for a project, optionally filtered by type."""
    query = (
        select(MessageLog)
        .where(MessageLog.project_id == project_id)
        .order_by(MessageLog.created_at)
    )
    if type is not None:
        query = query.where(MessageLog.message_type == type.value)
    result = await db.execute(query)
    return list(result.scalars().all())


def create_brief_message(
    from_agent: str,
    to_agent: str,
    project_id: str,
    objective: str,
    context: dict | None = None,
    constraints: list[str] | None = None,
    expected_deliverables: list[str] | None = None,
) -> AgentMessage:
    """Factory for BRIEF messages — work requests from one agent to another."""
    return AgentMessage(
        id=str(uuid.uuid4()),
        type=MessageType.BRIEF,
        from_agent=from_agent,
        to_agent=to_agent,
        project_id=project_id,
        timestamp=datetime.utcnow(),
        objective=objective,
        context=context,
        constraints=constraints,
        expected_deliverables=expected_deliverables,
    )


def create_handoff_message(
    from_agent: str,
    to_agent: str,
    project_id: str,
    summary: str,
    content: str,
    artifacts: list[dict] | None = None,
) -> AgentMessage:
    """Factory for HANDOFF messages — completed deliverables passed downstream."""
    return AgentMessage(
        id=str(uuid.uuid4()),
        type=MessageType.HANDOFF,
        from_agent=from_agent,
        to_agent=to_agent,
        project_id=project_id,
        timestamp=datetime.utcnow(),
        summary=summary,
        notes=content,
        artifacts=artifacts,
    )
