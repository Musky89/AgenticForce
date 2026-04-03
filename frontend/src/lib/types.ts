export type ProjectStatus =
  | "draft"
  | "briefed"
  | "in_progress"
  | "review"
  | "revision"
  | "approved"
  | "delivered";

export type AgentRole =
  | "creative_director"
  | "strategist"
  | "copywriter"
  | "art_director"
  | "researcher"
  | "brand_voice";

export type RunStatus = "queued" | "running" | "completed" | "failed";

export interface Client {
  id: string;
  name: string;
  industry: string | null;
  website: string | null;
  brand_guidelines: string | null;
  tone_keywords: string | null;
  target_audience: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
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
  created_at: string;
  updated_at: string;
}

export interface AgentRun {
  id: string;
  project_id: string;
  agent_role: AgentRole;
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
  created_at: string;
}

export interface DashboardStats {
  total_clients: number;
  total_projects: number;
  projects_in_progress: number;
  projects_delivered: number;
  total_agent_runs: number;
  total_deliverables: number;
}

export interface PipelineRunResult {
  project_id: string;
  runs: AgentRun[];
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
  quality: string;
  style: string;
  created_at: string;
}
