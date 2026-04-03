from pydantic import BaseModel, Field
from datetime import datetime
from app.models.models import ProjectStatus, AgentRole, RunStatus, BlueprintTemplate, PipelineStage


# --- Client ---

class ClientCreate(BaseModel):
    name: str
    industry: str | None = None
    website: str | None = None
    notes: str | None = None


class ClientUpdate(BaseModel):
    name: str | None = None
    industry: str | None = None
    website: str | None = None
    notes: str | None = None


class ClientOut(BaseModel):
    id: str
    name: str
    industry: str | None
    website: str | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Brand Bible ---

class BrandBibleCreate(BaseModel):
    client_id: str
    brand_essence: str | None = None
    mission: str | None = None
    vision: str | None = None
    values: str | None = None
    positioning_statement: str | None = None
    unique_selling_proposition: str | None = None
    primary_audience: str | None = None
    secondary_audience: str | None = None
    audience_personas: dict | None = None
    color_palette: dict | None = None
    typography: dict | None = None
    photography_style: str | None = None
    illustration_style: str | None = None
    composition_rules: str | None = None
    logo_usage: str | None = None
    visual_dos: str | None = None
    visual_donts: str | None = None
    tone_of_voice: str | None = None
    voice_attributes: dict | None = None
    vocabulary_preferences: str | None = None
    vocabulary_avoid: str | None = None
    headline_style: str | None = None
    copy_style: str | None = None
    competitors: dict | None = None
    differentiation: str | None = None
    social_guidelines: dict | None = None
    email_guidelines: dict | None = None
    print_guidelines: dict | None = None
    web_guidelines: dict | None = None


class BrandBibleUpdate(BrandBibleCreate):
    client_id: str | None = None


class BrandBibleOut(BaseModel):
    id: str
    client_id: str
    brand_essence: str | None
    mission: str | None
    vision: str | None
    values: str | None
    positioning_statement: str | None
    unique_selling_proposition: str | None
    primary_audience: str | None
    secondary_audience: str | None
    audience_personas: dict | None
    color_palette: dict | None
    typography: dict | None
    photography_style: str | None
    illustration_style: str | None
    composition_rules: str | None
    logo_usage: str | None
    visual_dos: str | None
    visual_donts: str | None
    tone_of_voice: str | None
    voice_attributes: dict | None
    vocabulary_preferences: str | None
    vocabulary_avoid: str | None
    headline_style: str | None
    copy_style: str | None
    competitors: dict | None
    differentiation: str | None
    social_guidelines: dict | None
    email_guidelines: dict | None
    print_guidelines: dict | None
    web_guidelines: dict | None
    version: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- Service Blueprint ---

class ServiceBlueprintCreate(BaseModel):
    client_id: str
    template_type: BlueprintTemplate
    active_services: dict | None = None
    recurring_briefs: dict | None = None
    quality_thresholds: dict | None = None
    budget_params: dict | None = None
    special_pipelines: dict | None = None
    approval_rules: dict | None = None
    lora_config: dict | None = None
    integrations: dict | None = None


class ServiceBlueprintUpdate(BaseModel):
    template_type: BlueprintTemplate | None = None
    active_services: dict | None = None
    recurring_briefs: dict | None = None
    quality_thresholds: dict | None = None
    budget_params: dict | None = None
    special_pipelines: dict | None = None
    approval_rules: dict | None = None
    lora_config: dict | None = None
    integrations: dict | None = None


class ServiceBlueprintOut(BaseModel):
    id: str
    client_id: str
    template_type: BlueprintTemplate
    active_services: dict | None
    recurring_briefs: dict | None
    quality_thresholds: dict | None
    budget_params: dict | None
    special_pipelines: dict | None
    approval_rules: dict | None
    lora_config: dict | None
    integrations: dict | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# --- LoRA ---

class LoRAModelCreate(BaseModel):
    client_id: str
    name: str
    base_model: str = "fal-ai/flux-lora"
    trigger_word: str | None = None
    training_images_count: int | None = None


class LoRAModelOut(BaseModel):
    id: str
    client_id: str
    name: str
    status: str
    base_model: str
    weights_url: str | None
    trigger_word: str | None
    training_steps: int | None
    training_images_count: int | None
    version: int
    created_at: datetime
    last_trained_at: datetime | None

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
    desired_emotional_response: str | None = None
    mandatory_inclusions: str | None = None
    competitive_differentiation: str | None = None
    output_formats: dict | None = None


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
    desired_emotional_response: str | None = None
    mandatory_inclusions: str | None = None
    competitive_differentiation: str | None = None
    output_formats: dict | None = None


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
    desired_emotional_response: str | None
    mandatory_inclusions: str | None
    competitive_differentiation: str | None
    output_formats: dict | None
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
    pipeline_stage: PipelineStage | None
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
    generate_images: bool = True
    run_quality_scoring: bool = True


class AgentListRunRequest(BaseModel):
    project_id: str
    agents: list[AgentRole] = Field(default=[
        AgentRole.RESEARCHER, AgentRole.STRATEGIST, AgentRole.BRAND_VOICE,
        AgentRole.CREATIVE_DIRECTOR, AgentRole.ART_DIRECTOR,
        AgentRole.COPYWRITER, AgentRole.DESIGNER,
    ])
    generate_images: bool = False


class PipelineRunOut(BaseModel):
    project_id: str
    runs: list[AgentRunOut]


# --- Generated Images ---

class ImageGenerateRequest(BaseModel):
    prompt: str
    project_id: str | None = None
    width: int = 1024
    height: int = 1024
    num_images: int = 1
    use_client_lora: bool = False


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
    quality_score: float | None
    quality_breakdown: dict | None
    is_approved: bool
    is_rejected: bool
    rejection_reason: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


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
    pipeline_stage: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Creative Memory ---

class CreativeMemoryCreate(BaseModel):
    client_id: str
    memory_type: str
    content: str
    category: str | None = None
    metadata_json: dict | None = None
    effectiveness_score: float | None = None


class CreativeMemoryOut(BaseModel):
    id: str
    client_id: str
    memory_type: str
    category: str | None
    content: str
    metadata_json: dict | None
    effectiveness_score: float | None
    times_used: int
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
    total_images: int
    total_lora_models: int
