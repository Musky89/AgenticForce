import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Enum as SAEnum, JSON, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


def gen_uuid() -> str:
    return str(uuid.uuid4())


class ProjectStatus(str, enum.Enum):
    DRAFT = "draft"
    BRIEFED = "briefed"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    REVISION = "revision"
    APPROVED = "approved"
    DELIVERED = "delivered"


class AgentRole(str, enum.Enum):
    CREATIVE_DIRECTOR = "creative_director"
    STRATEGIST = "strategist"
    COPYWRITER = "copywriter"
    ART_DIRECTOR = "art_director"
    RESEARCHER = "researcher"
    BRAND_VOICE = "brand_voice"


class RunStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(255))
    website: Mapped[str | None] = mapped_column(String(512))
    brand_guidelines: Mapped[str | None] = mapped_column(Text)
    tone_keywords: Mapped[str | None] = mapped_column(Text)
    target_audience: Mapped[str | None] = mapped_column(Text)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    projects: Mapped[list["Project"]] = relationship(back_populates="client", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    client_id: Mapped[str] = mapped_column(ForeignKey("clients.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ProjectStatus] = mapped_column(
        SAEnum(ProjectStatus), default=ProjectStatus.DRAFT
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    client: Mapped["Client"] = relationship(back_populates="projects")
    brief: Mapped["Brief | None"] = relationship(back_populates="project", uselist=False, cascade="all, delete-orphan")
    agent_runs: Mapped[list["AgentRun"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    deliverables: Mapped[list["Deliverable"]] = relationship(back_populates="project", cascade="all, delete-orphan")


class Brief(Base):
    __tablename__ = "briefs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), unique=True, nullable=False)
    objective: Mapped[str] = mapped_column(Text, nullable=False)
    deliverables_description: Mapped[str | None] = mapped_column(Text)
    target_audience: Mapped[str | None] = mapped_column(Text)
    key_messages: Mapped[str | None] = mapped_column(Text)
    tone: Mapped[str | None] = mapped_column(String(255))
    constraints: Mapped[str | None] = mapped_column(Text)
    inspiration: Mapped[str | None] = mapped_column(Text)
    budget_notes: Mapped[str | None] = mapped_column(Text)
    additional_context: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project: Mapped["Project"] = relationship(back_populates="brief")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    agent_role: Mapped[AgentRole] = mapped_column(SAEnum(AgentRole), nullable=False)
    status: Mapped[RunStatus] = mapped_column(SAEnum(RunStatus), default=RunStatus.QUEUED)
    input_data: Mapped[dict | None] = mapped_column(JSON)
    output_data: Mapped[dict | None] = mapped_column(JSON)
    tokens_used: Mapped[int | None] = mapped_column()
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)

    project: Mapped["Project"] = relationship(back_populates="agent_runs")


class Deliverable(Base):
    __tablename__ = "deliverables"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    agent_run_id: Mapped[str | None] = mapped_column(ForeignKey("agent_runs.id"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(default=1)
    is_approved: Mapped[bool] = mapped_column(default=False)
    feedback: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["Project"] = relationship(back_populates="deliverables")
    agent_run: Mapped["AgentRun | None"] = relationship()
