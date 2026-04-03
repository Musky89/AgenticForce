export type ProjectStatus =
  | "draft"
  | "briefed"
  | "in_progress"
  | "review"
  | "revision"
  | "approved"
  | "delivered";

export type AgentRole =
  | "strategist"
  | "creative_director"
  | "art_director"
  | "designer"
  | "copywriter"
  | "researcher"
  | "brand_voice"
  | "quality_scorer"
  | "community_manager"
  | "media_buyer"
  | "email_specialist"
  | "seo_specialist"
  | "producer";

export type RunStatus = "queued" | "running" | "completed" | "failed";

export type BlueprintTemplate =
  | "social_first"
  | "performance"
  | "content_led"
  | "new_brand"
  | "traditional_media"
  | "full_service";

export type PipelineStage =
  | "strategic_framing"
  | "concept_exploration"
  | "art_direction"
  | "visual_generation"
  | "refinement"
  | "quality_scoring";

export interface Client {
  id: string;
  name: string;
  industry: string | null;
  website: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface BrandBible {
  id: string;
  client_id: string;
  brand_essence: string | null;
  mission: string | null;
  vision: string | null;
  values: string | null;
  positioning_statement: string | null;
  unique_selling_proposition: string | null;
  primary_audience: string | null;
  secondary_audience: string | null;
  audience_personas: Record<string, unknown> | null;
  color_palette: { primary?: string[]; secondary?: string[]; accent?: string[] } | null;
  typography: Record<string, unknown> | null;
  photography_style: string | null;
  illustration_style: string | null;
  composition_rules: string | null;
  logo_usage: string | null;
  visual_dos: string | null;
  visual_donts: string | null;
  tone_of_voice: string | null;
  voice_attributes: { is?: string[]; is_not?: string[] } | null;
  vocabulary_preferences: string | null;
  vocabulary_avoid: string | null;
  headline_style: string | null;
  copy_style: string | null;
  competitors: Record<string, unknown> | null;
  differentiation: string | null;
  social_guidelines: Record<string, unknown> | null;
  email_guidelines: Record<string, unknown> | null;
  print_guidelines: Record<string, unknown> | null;
  web_guidelines: Record<string, unknown> | null;
  version: number;
  created_at: string;
  updated_at: string;
}

export interface ServiceBlueprint {
  id: string;
  client_id: string;
  template_type: BlueprintTemplate;
  active_services: Record<string, unknown> | null;
  recurring_briefs: Record<string, unknown> | null;
  quality_thresholds: Record<string, unknown> | null;
  budget_params: Record<string, unknown> | null;
  special_pipelines: Record<string, unknown> | null;
  approval_rules: Record<string, unknown> | null;
  lora_config: Record<string, unknown> | null;
  integrations: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface LoRAModel {
  id: string;
  client_id: string;
  name: string;
  status: string;
  base_model: string;
  weights_url: string | null;
  trigger_word: string | null;
  training_steps: number | null;
  training_images_count: number | null;
  version: number;
  created_at: string;
  last_trained_at: string | null;
}

export interface Project {
  id: string;
  client_id: string;
  name: string;
  status: ProjectStatus;
  created_at: string;
  updated_at: string;
}

export interface ProjectDetail extends Project {
  client: Client;
  brief: Brief | null;
}

export interface Brief {
  id: string;
  project_id: string;
  objective: string;
  deliverables_description: string | null;
  target_audience: string | null;
  key_messages: string | null;
  tone: string | null;
  constraints: string | null;
  inspiration: string | null;
  budget_notes: string | null;
  additional_context: string | null;
  desired_emotional_response: string | null;
  mandatory_inclusions: string | null;
  competitive_differentiation: string | null;
  output_formats: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}

export interface AgentRun {
  id: string;
  project_id: string;
  agent_role: AgentRole;
  pipeline_stage: PipelineStage | null;
  status: RunStatus;
  input_data: Record<string, unknown> | null;
  output_data: Record<string, unknown> | null;
  tokens_used: number | null;
  duration_seconds: number | null;
  error_message: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface Deliverable {
  id: string;
  project_id: string;
  agent_run_id: string | null;
  title: string;
  content_type: string;
  content: string;
  version: number;
  is_approved: boolean;
  feedback: string | null;
  metadata_json: Record<string, unknown> | null;
  pipeline_stage: string | null;
  created_at: string;
}

export interface GeneratedImage {
  id: string;
  project_id: string | null;
  agent_run_id: string | null;
  filename: string;
  prompt: string;
  revised_prompt: string | null;
  label: string | null;
  size: string;
  provider: string;
  quality_score: number | null;
  quality_breakdown: Record<string, unknown> | null;
  is_approved: boolean;
  is_rejected: boolean;
  rejection_reason: string | null;
  created_at: string;
}

export interface DashboardStats {
  total_clients: number;
  total_projects: number;
  projects_in_progress: number;
  projects_delivered: number;
  total_agent_runs: number;
  total_deliverables: number;
  total_images: number;
  total_lora_models: number;
}

export interface PipelineRunResult {
  project_id: string;
  runs: AgentRun[];
}

export interface OrchestratorTask {
  id: string;
  project_id: string;
  agent_role: string;
  pipeline_stage: string | null;
  title: string;
  description: string | null;
  status: string;
  sort_order: number;
  depends_on: string[] | null;
  requires_review: boolean;
  agent_run_id: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface ReviewItem {
  id: string;
  project_id: string;
  task_id: string | null;
  deliverable_id: string | null;
  image_id: string | null;
  title: string;
  item_type: string;
  status: string;
  quality_score: number | null;
  feedback: string | null;
  priority: number;
  created_at: string;
  reviewed_at: string | null;
}

export interface ReviewQueueStats {
  pending: number;
  approved: number;
  revision_requested: number;
  total: number;
}
