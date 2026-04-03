import type {
  Client,
  Project,
  ProjectDetail,
  Brief,
  AgentRun,
  AgentRole,
  Deliverable,
  DashboardStats,
  PipelineRunResult,
  GeneratedImage,
  BrandBible,
  ServiceBlueprint,
  BlueprintTemplate,
  LoRAModel,
} from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  if (res.status === 204) return undefined as T;
  return res.json();
}

export const api = {
  // Dashboard
  getStats: () => request<DashboardStats>("/dashboard/stats"),

  // Clients
  listClients: () => request<Client[]>("/clients"),
  getClient: (id: string) => request<Client>(`/clients/${id}`),
  createClient: (data: Partial<Client>) =>
    request<Client>("/clients", { method: "POST", body: JSON.stringify(data) }),
  updateClient: (id: string, data: Partial<Client>) =>
    request<Client>(`/clients/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteClient: (id: string) =>
    request<void>(`/clients/${id}`, { method: "DELETE" }),

  // Brand Bible
  getBrandBible: (clientId: string) =>
    request<BrandBible>(`/brand-bibles/client/${clientId}`),
  createBrandBible: (data: Partial<BrandBible> & { client_id: string }) =>
    request<BrandBible>("/brand-bibles", { method: "POST", body: JSON.stringify(data) }),
  updateBrandBible: (id: string, data: Partial<BrandBible>) =>
    request<BrandBible>(`/brand-bibles/${id}`, { method: "PATCH", body: JSON.stringify(data) }),

  // Service Blueprints
  getBlueprintTemplates: () =>
    request<{ value: string; label: string; defaults: Record<string, unknown> }[]>("/blueprints/templates"),
  getBlueprint: (clientId: string) =>
    request<ServiceBlueprint>(`/blueprints/client/${clientId}`),
  createBlueprint: (data: { client_id: string; template_type: BlueprintTemplate }) =>
    request<ServiceBlueprint>("/blueprints", { method: "POST", body: JSON.stringify(data) }),
  updateBlueprint: (id: string, data: Partial<ServiceBlueprint>) =>
    request<ServiceBlueprint>(`/blueprints/${id}`, { method: "PATCH", body: JSON.stringify(data) }),

  // LoRA
  listClientLoras: (clientId: string) =>
    request<LoRAModel[]>(`/lora/client/${clientId}`),
  createLora: (data: { client_id: string; name: string; trigger_word?: string }) =>
    request<LoRAModel>("/lora", { method: "POST", body: JSON.stringify(data) }),
  updateLora: (id: string, data: Record<string, unknown>) =>
    request<LoRAModel>(`/lora/${id}`, { method: "PATCH", body: JSON.stringify(data) }),

  // Projects
  listProjects: (clientId?: string) =>
    request<Project[]>(`/projects${clientId ? `?client_id=${clientId}` : ""}`),
  getProject: (id: string) => request<ProjectDetail>(`/projects/${id}`),
  createProject: (data: { client_id: string; name: string }) =>
    request<Project>("/projects", { method: "POST", body: JSON.stringify(data) }),
  updateProject: (id: string, data: Partial<Project>) =>
    request<Project>(`/projects/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteProject: (id: string) =>
    request<void>(`/projects/${id}`, { method: "DELETE" }),

  // Briefs
  getBriefByProject: (projectId: string) =>
    request<Brief>(`/briefs/project/${projectId}`),
  createBrief: (data: Partial<Brief> & { project_id: string; objective: string }) =>
    request<Brief>("/briefs", { method: "POST", body: JSON.stringify(data) }),
  updateBrief: (id: string, data: Partial<Brief>) =>
    request<Brief>(`/briefs/${id}`, { method: "PATCH", body: JSON.stringify(data) }),

  // Agents
  getRoles: () => request<{ value: string; label: string }[]>("/agents/roles"),
  getPipelineStages: () => request<{ value: string; label: string }[]>("/agents/pipeline-stages"),
  runAgent: (data: { project_id: string; agent_role: AgentRole; input_data?: Record<string, unknown> }) =>
    request<AgentRun>("/agents/run", { method: "POST", body: JSON.stringify(data) }),
  runCreativePipeline: (data: { project_id: string; generate_images?: boolean; run_quality_scoring?: boolean }) =>
    request<PipelineRunResult>("/agents/pipeline", { method: "POST", body: JSON.stringify(data) }),
  runAgentList: (data: { project_id: string; agents?: AgentRole[]; generate_images?: boolean }) =>
    request<PipelineRunResult>("/agents/agent-list", { method: "POST", body: JSON.stringify(data) }),
  listRuns: (projectId?: string) =>
    request<AgentRun[]>(`/agents/runs${projectId ? `?project_id=${projectId}` : ""}`),
  getRun: (id: string) => request<AgentRun>(`/agents/runs/${id}`),

  // Deliverables
  listDeliverables: (projectId?: string) =>
    request<Deliverable[]>(`/deliverables${projectId ? `?project_id=${projectId}` : ""}`),
  getDeliverable: (id: string) => request<Deliverable>(`/deliverables/${id}`),
  updateDeliverable: (id: string, data: Partial<Deliverable>) =>
    request<Deliverable>(`/deliverables/${id}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteDeliverable: (id: string) =>
    request<void>(`/deliverables/${id}`, { method: "DELETE" }),

  // Images
  listImages: (projectId?: string) =>
    request<GeneratedImage[]>(`/images${projectId ? `?project_id=${projectId}` : ""}`),
  getImageProviders: () =>
    request<{ providers: { id: string; name: string; supports_lora: boolean }[]; default: string }>("/images/providers"),
  generateImage: (data: { prompt: string; project_id?: string; width?: number; height?: number; num_images?: number; use_client_lora?: boolean; provider?: string; aspect_ratio?: string }) =>
    request<GeneratedImage[]>("/images/generate", { method: "POST", body: JSON.stringify(data) }),
  generateFromArtDirection: (projectId: string, provider?: string) =>
    request<GeneratedImage[]>("/images/from-art-direction", { method: "POST", body: JSON.stringify({ project_id: projectId, provider }) }),
  scoreImage: (imageId: string) =>
    request<GeneratedImage>(`/images/${imageId}/score`, { method: "POST" }),
  approveImage: (imageId: string) =>
    request<GeneratedImage>(`/images/${imageId}/approve`, { method: "PATCH" }),
  deleteImage: (id: string) =>
    request<void>(`/images/${id}`, { method: "DELETE" }),
  getImageUrl: (id: string) => `${API_BASE}/images/${id}/file`,

  // Orchestrator
  decomposeBrief: (projectId: string) =>
    request<{ project_id: string; tasks: import("./types").OrchestratorTask[] }>(`/orchestrator/decompose/${projectId}`, { method: "POST" }),
  getTaskGraph: (projectId: string) =>
    request<import("./types").OrchestratorTask[]>(`/orchestrator/tasks/${projectId}`),
  executeNextTask: (projectId: string) =>
    request<import("./types").OrchestratorTask | null>(`/orchestrator/execute/${projectId}`, { method: "POST" }),
  executeAllReady: (projectId: string) =>
    request<import("./types").OrchestratorTask[]>(`/orchestrator/execute-all/${projectId}`, { method: "POST" }),
  approveTask: (taskId: string, feedback?: string) =>
    request<import("./types").OrchestratorTask>(`/orchestrator/approve/${taskId}`, { method: "POST", body: JSON.stringify({ feedback }) }),
  requestRevision: (taskId: string, feedback: string) =>
    request<import("./types").OrchestratorTask>(`/orchestrator/revise/${taskId}`, { method: "POST", body: JSON.stringify({ feedback }) }),

  // Review Queue
  getReviewQueue: (status?: string, projectId?: string) => {
    const params = new URLSearchParams();
    if (status) params.set("status", status);
    if (projectId) params.set("project_id", projectId);
    const qs = params.toString();
    return request<import("./types").ReviewItem[]>(`/review/queue${qs ? `?${qs}` : ""}`);
  },
  getReviewStats: () => request<import("./types").ReviewQueueStats>("/review/stats"),
  reviewAction: (itemId: string, status: string, feedback?: string) =>
    request<import("./types").ReviewItem>(`/review/${itemId}/action`, { method: "POST", body: JSON.stringify({ status, feedback }) }),

  // Export
  exportStrategyPdf: (projectId: string) => `${API_BASE}/export/strategy/${projectId}`,
  exportConceptsPptx: (projectId: string) => `${API_BASE}/export/concepts/${projectId}`,
  exportDeliverablesPdf: (projectId: string) => `${API_BASE}/export/deliverables/${projectId}`,
};
