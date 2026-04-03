from pydantic import BaseModel, Field
from datetime import datetime
from app.models.models import ProjectStatus, AgentRole, RunStatus


# --- Client ---

class ClientCreate(BaseModel):
    name: str
    industry: str | None = None
    website: str | None = None
    brand_guidelines: str | None = None
    tone_keywords: str | None = None
    target_audience: str | None = None
    notes: str | None = None


class ClientUpdate(BaseModel):
    name: str | None = None
    industry: str | None = None
    website: str | None = None
    brand_guidelines: str | None = None
    tone_keywords: str | None = None
    target_audience: str | None = None
    notes: str | None = None


class ClientOut(BaseModel):
    id: str
    name: str
    industry: str | None
    website: str | None
    brand_guidelines: str | None
    tone_keywords: str | None
    target_audience: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Project ---

class ProjectCreate(BaseModel):
    client_id: str
    name: str


class ProjectUpdate(BaseModel):
    name: str | None = None
    status: ProjectStatus | None = None


class ProjectOut(BaseModel):
    id: str
    client_id: str
    name: str
    status: ProjectStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectDetail(ProjectOut):
    client: ClientOut
    brief: "BriefOut | None" = None

    model_config = {"from_attributes": True}


# --- Brief ---

class BriefCreate(BaseModel):
    project_id: str
    objective: str
    deliverables_description: str | None = None
    target_audience: str | None = None
    key_messages: str | None = None
    tone: str | None = None
    constraints: str | None = None
    inspiration: str | None = None
    budget_notes: str | None = None
    additional_context: str | None = None


class BriefUpdate(BaseModel):
    objective: str | None = None
    deliverables_description: str | None = None
    target_audience: str | None = None
    key_messages: str | None = None
    tone: str | None = None
    constraints: str | None = None
    inspiration: str | None = None
    budget_notes: str | None = None
    additional_context: str | None = None


class BriefOut(BaseModel):
    id: str
    project_id: str
    objective: str
    deliverables_description: str | None
    target_audience: str | None
    key_messages: str | None
    tone: str | None
    constraints: str | None
    inspiration: str | None
    budget_notes: str | None
    additional_context: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Agent Run ---

class AgentRunRequest(BaseModel):
    project_id: str
    agent_role: AgentRole
    input_data: dict | None = None


class AgentRunOut(BaseModel):
    id: str
    project_id: str
    agent_role: AgentRole
    status: RunStatus
    input_data: dict | None
    output_data: dict | None
    tokens_used: int | None
    duration_seconds: float | None
    error_message: str | None
    created_at: datetime
    completed_at: datetime | None

    model_config = {"from_attributes": True}


class PipelineRunRequest(BaseModel):
    project_id: str
    agents: list[AgentRole] = Field(
        default=[
            AgentRole.RESEARCHER,
            AgentRole.STRATEGIST,
            AgentRole.BRAND_VOICE,
            AgentRole.COPYWRITER,
            AgentRole.ART_DIRECTOR,
            AgentRole.CREATIVE_DIRECTOR,
        ]
    )
    generate_images: bool = False


class PipelineRunOut(BaseModel):
    project_id: str
    runs: list[AgentRunOut]


# --- Deliverable ---

class DeliverableCreate(BaseModel):
    project_id: str
    agent_run_id: str | None = None
    title: str
    content_type: str
    content: str
    metadata_json: dict | None = None


class DeliverableUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    is_approved: bool | None = None
    feedback: str | None = None


class DeliverableOut(BaseModel):
    id: str
    project_id: str
    agent_run_id: str | None
    title: str
    content_type: str
    content: str
    version: int
    is_approved: bool
    feedback: str | None
    metadata_json: dict | None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Generated Images ---

class ImageGenerateRequest(BaseModel):
    prompt: str
    project_id: str | None = None
    size: str = "1024x1024"
    quality: str = "standard"
    style: str = "vivid"


class ImageFromArtDirectionRequest(BaseModel):
    project_id: str


class GeneratedImageOut(BaseModel):
    id: str
    project_id: str | None
    agent_run_id: str | None
    filename: str
    prompt: str
    revised_prompt: str | None
    label: str | None
    size: str
    quality: str
    style: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Dashboard ---

class DashboardStats(BaseModel):
    total_clients: int
    total_projects: int
    projects_in_progress: int
    projects_delivered: int
    total_agent_runs: int
    total_deliverables: int
