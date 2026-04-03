import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Enum as SAEnum, JSON, Float, Boolean, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


def gen_uuid() -> str:
    return str(uuid.uuid4())


# --- Enums ---

class ProjectStatus(str, enum.Enum):
    DRAFT = "draft"
    BRIEFED = "briefed"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    REVISION = "revision"
    APPROVED = "approved"
    DELIVERED = "delivered"


class AgentRole(str, enum.Enum):
    STRATEGIST = "strategist"
    CREATIVE_DIRECTOR = "creative_director"
    ART_DIRECTOR = "art_director"
    DESIGNER = "designer"
    COPYWRITER = "copywriter"
    RESEARCHER = "researcher"
    BRAND_VOICE = "brand_voice"
    QUALITY_SCORER = "quality_scorer"
    COMMUNITY_MANAGER = "community_manager"
    MEDIA_BUYER = "media_buyer"
    EMAIL_SPECIALIST = "email_specialist"
    SEO_SPECIALIST = "seo_specialist"
    PRODUCER = "producer"


class RunStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class BlueprintTemplate(str, enum.Enum):
    SOCIAL_FIRST = "social_first"
    PERFORMANCE = "performance"
    CONTENT_LED = "content_led"
    NEW_BRAND = "new_brand"
    TRADITIONAL_MEDIA = "traditional_media"
    FULL_SERVICE = "full_service"


class PipelineStage(str, enum.Enum):
    STRATEGIC_FRAMING = "strategic_framing"
    CONCEPT_EXPLORATION = "concept_exploration"
    ART_DIRECTION = "art_direction"
    VISUAL_GENERATION = "visual_generation"
    REFINEMENT = "refinement"
    QUALITY_SCORING = "quality_scoring"


# --- Models ---

class Client(Base):
    __tablename__ = "clients"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(255))
    website: Mapped[str | None] = mapped_column(String(512))
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    projects: Mapped[list["Project"]] = relationship(back_populates="client", cascade="all, delete-orphan")
    brand_bible: Mapped["BrandBible | None"] = relationship(back_populates="client", uselist=False, cascade="all, delete-orphan")
    service_blueprint: Mapped["ServiceBlueprint | None"] = relationship(back_populates="client", uselist=False, cascade="all, delete-orphan")
    lora_models: Mapped[list["LoRAModel"]] = relationship(back_populates="client", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class BrandBible(Base):
    """Structured brand context that feeds every agent — the brand's DNA encoded as data."""
    __tablename__ = "brand_bibles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    client_id: Mapped[str] = mapped_column(ForeignKey("clients.id"), unique=True, nullable=False)

    # Brand Positioning
    brand_essence: Mapped[str | None] = mapped_column(Text)
    mission: Mapped[str | None] = mapped_column(Text)
    vision: Mapped[str | None] = mapped_column(Text)
    values: Mapped[str | None] = mapped_column(Text)
    positioning_statement: Mapped[str | None] = mapped_column(Text)
    unique_selling_proposition: Mapped[str | None] = mapped_column(Text)

    # Target Audience
    primary_audience: Mapped[str | None] = mapped_column(Text)
    secondary_audience: Mapped[str | None] = mapped_column(Text)
    audience_personas: Mapped[dict | None] = mapped_column(JSON)

    # Visual Identity
    color_palette: Mapped[dict | None] = mapped_column(JSON)  # {primary: [], secondary: [], accent: []}
    typography: Mapped[dict | None] = mapped_column(JSON)  # {headings: {}, body: {}, accent: {}}
    photography_style: Mapped[str | None] = mapped_column(Text)
    illustration_style: Mapped[str | None] = mapped_column(Text)
    composition_rules: Mapped[str | None] = mapped_column(Text)
    logo_usage: Mapped[str | None] = mapped_column(Text)
    visual_dos: Mapped[str | None] = mapped_column(Text)
    visual_donts: Mapped[str | None] = mapped_column(Text)

    # Verbal Identity
    tone_of_voice: Mapped[str | None] = mapped_column(Text)
    voice_attributes: Mapped[dict | None] = mapped_column(JSON)  # {is: [], is_not: []}
    vocabulary_preferences: Mapped[str | None] = mapped_column(Text)
    vocabulary_avoid: Mapped[str | None] = mapped_column(Text)
    headline_style: Mapped[str | None] = mapped_column(Text)
    copy_style: Mapped[str | None] = mapped_column(Text)

    # Competitive Landscape
    competitors: Mapped[dict | None] = mapped_column(JSON)
    differentiation: Mapped[str | None] = mapped_column(Text)

    # Channel-Specific Guidelines
    social_guidelines: Mapped[dict | None] = mapped_column(JSON)
    email_guidelines: Mapped[dict | None] = mapped_column(JSON)
    print_guidelines: Mapped[dict | None] = mapped_column(JSON)
    web_guidelines: Mapped[dict | None] = mapped_column(JSON)

    # Metadata
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    client: Mapped["Client"] = relationship(back_populates="brand_bible")


class ServiceBlueprint(Base):
    """Machine-readable retainer agreement — defines what the platform does for each client."""
    __tablename__ = "service_blueprints"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    client_id: Mapped[str] = mapped_column(ForeignKey("clients.id"), unique=True, nullable=False)
    template_type: Mapped[BlueprintTemplate] = mapped_column(SAEnum(BlueprintTemplate), nullable=False)

    active_services: Mapped[dict | None] = mapped_column(JSON)  # [{service, cadence, output_specs, agents}]
    recurring_briefs: Mapped[dict | None] = mapped_column(JSON)  # [{schedule, template, params}]
    quality_thresholds: Mapped[dict | None] = mapped_column(JSON)  # {color: 15, clip: 0.75, ...}
    budget_params: Mapped[dict | None] = mapped_column(JSON)  # {monthly_media, freelancer_cap}
    special_pipelines: Mapped[dict | None] = mapped_column(JSON)  # [{garment_compositing, print_production}]
    approval_rules: Mapped[dict | None] = mapped_column(JSON)  # {auto_publish: [], founder_review: []}
    lora_config: Mapped[dict | None] = mapped_column(JSON)  # {model_id, retraining_schedule}
    integrations: Mapped[dict | None] = mapped_column(JSON)  # {meta: {}, google: {}, mailchimp: {}}

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    client: Mapped["Client"] = relationship(back_populates="service_blueprint")


class LoRAModel(Base):
    """Per-client fine-tuned LoRA model — the brand's visual DNA at the model weight level."""
    __tablename__ = "lora_models"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    client_id: Mapped[str] = mapped_column(ForeignKey("clients.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")  # pending, training, ready, failed
    base_model: Mapped[str] = mapped_column(String(255), default="fal-ai/flux-lora")
    training_data_path: Mapped[str | None] = mapped_column(String(512))
    weights_url: Mapped[str | None] = mapped_column(String(512))
    trigger_word: Mapped[str | None] = mapped_column(String(100))
    training_steps: Mapped[int | None] = mapped_column(Integer)
    training_images_count: Mapped[int | None] = mapped_column(Integer)
    training_config: Mapped[dict | None] = mapped_column(JSON)
    version: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_trained_at: Mapped[datetime | None] = mapped_column(DateTime)

    client: Mapped["Client"] = relationship(back_populates="lora_models")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    client_id: Mapped[str] = mapped_column(ForeignKey("clients.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ProjectStatus] = mapped_column(SAEnum(ProjectStatus), default=ProjectStatus.DRAFT)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    client: Mapped["Client"] = relationship(back_populates="projects")
    brief: Mapped["Brief | None"] = relationship(back_populates="project", uselist=False, cascade="all, delete-orphan")
    agent_runs: Mapped[list["AgentRun"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    deliverables: Mapped[list["Deliverable"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    generated_images: Mapped[list["GeneratedImage"]] = relationship(back_populates="project", cascade="all, delete-orphan")


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
    desired_emotional_response: Mapped[str | None] = mapped_column(Text)
    mandatory_inclusions: Mapped[str | None] = mapped_column(Text)
    competitive_differentiation: Mapped[str | None] = mapped_column(Text)
    output_formats: Mapped[dict | None] = mapped_column(JSON)  # [{format, dimensions, platform}]
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project: Mapped["Project"] = relationship(back_populates="brief")


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    agent_role: Mapped[AgentRole] = mapped_column(SAEnum(AgentRole), nullable=False)
    pipeline_stage: Mapped[PipelineStage | None] = mapped_column(SAEnum(PipelineStage))
    status: Mapped[RunStatus] = mapped_column(SAEnum(RunStatus), default=RunStatus.QUEUED)
    input_data: Mapped[dict | None] = mapped_column(JSON)
    output_data: Mapped[dict | None] = mapped_column(JSON)
    tokens_used: Mapped[int | None] = mapped_column()
    duration_seconds: Mapped[float | None] = mapped_column(Float)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)

    project: Mapped["Project"] = relationship(back_populates="agent_runs")


class GeneratedImage(Base):
    __tablename__ = "generated_images"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    project_id: Mapped[str | None] = mapped_column(ForeignKey("projects.id"))
    agent_run_id: Mapped[str | None] = mapped_column(ForeignKey("agent_runs.id"))
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    revised_prompt: Mapped[str | None] = mapped_column(Text)
    label: Mapped[str | None] = mapped_column(String(255))
    size: Mapped[str] = mapped_column(String(20), default="1024x1024")
    provider: Mapped[str] = mapped_column(String(20), default="flux")  # "flux" or "imagen"
    lora_model_id: Mapped[str | None] = mapped_column(ForeignKey("lora_models.id"))
    # Quality scoring fields
    quality_score: Mapped[float | None] = mapped_column(Float)
    quality_breakdown: Mapped[dict | None] = mapped_column(JSON)  # {color: 9, composition: 8, ...}
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    is_rejected: Mapped[bool] = mapped_column(Boolean, default=False)
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["Project | None"] = relationship(back_populates="generated_images")
    agent_run: Mapped["AgentRun | None"] = relationship()
    lora_model: Mapped["LoRAModel | None"] = relationship()


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
    pipeline_stage: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["Project"] = relationship(back_populates="deliverables")
    agent_run: Mapped["AgentRun | None"] = relationship()


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    BLOCKED = "blocked"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    AWAITING_REVIEW = "awaiting_review"
    APPROVED = "approved"
    REVISION_REQUESTED = "revision_requested"
    COMPLETED = "completed"
    FAILED = "failed"


class ReviewStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REVISION_REQUESTED = "revision_requested"
    REJECTED = "rejected"


class Task(Base):
    """Orchestrated unit of work — decomposes briefs into agent tasks with dependencies."""
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    agent_role: Mapped[AgentRole] = mapped_column(SAEnum(AgentRole), nullable=False)
    pipeline_stage: Mapped[PipelineStage | None] = mapped_column(SAEnum(PipelineStage))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[TaskStatus] = mapped_column(SAEnum(TaskStatus), default=TaskStatus.PENDING)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    depends_on: Mapped[dict | None] = mapped_column(JSON)  # [task_id, ...]
    input_context: Mapped[dict | None] = mapped_column(JSON)
    agent_run_id: Mapped[str | None] = mapped_column(ForeignKey("agent_runs.id"))
    requires_review: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)

    project: Mapped["Project"] = relationship()
    agent_run: Mapped["AgentRun | None"] = relationship()


class ReviewItem(Base):
    """The founder's review queue — quality-gated items requiring human judgment."""
    __tablename__ = "review_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    task_id: Mapped[str | None] = mapped_column(ForeignKey("tasks.id"))
    deliverable_id: Mapped[str | None] = mapped_column(ForeignKey("deliverables.id"))
    image_id: Mapped[str | None] = mapped_column(ForeignKey("generated_images.id"))
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    item_type: Mapped[str] = mapped_column(String(50), nullable=False)  # strategy, concept, art_direction, copy, visual, final
    status: Mapped[ReviewStatus] = mapped_column(SAEnum(ReviewStatus), default=ReviewStatus.PENDING)
    quality_score: Mapped[float | None] = mapped_column(Float)
    feedback: Mapped[str | None] = mapped_column(Text)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime)

    project: Mapped["Project"] = relationship()
    task: Mapped["Task | None"] = relationship()
    deliverable: Mapped["Deliverable | None"] = relationship()
    image: Mapped["GeneratedImage | None"] = relationship()


class MessageLog(Base):
    """Persisted inter-agent messages for audit and replay."""
    __tablename__ = "message_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"), nullable=False)
    message_type: Mapped[str] = mapped_column(String(20), nullable=False)
    from_agent: Mapped[str] = mapped_column(String(50), nullable=False)
    to_agent: Mapped[str | None] = mapped_column(String(50))
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["Project"] = relationship()


class CreativeMemory(Base):
    """Performance-linked creative memory — compounds over time."""
    __tablename__ = "creative_memory"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=gen_uuid)
    client_id: Mapped[str] = mapped_column(ForeignKey("clients.id"), nullable=False)
    memory_type: Mapped[str] = mapped_column(String(50), nullable=False)  # prompt, style, performance, pattern
    category: Mapped[str | None] = mapped_column(String(100))
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSON)
    effectiveness_score: Mapped[float | None] = mapped_column(Float)
    times_used: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
