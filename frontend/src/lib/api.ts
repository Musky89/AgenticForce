import type {
  Client,
  Project,
  ProjectDetail,
  Brief,
  AgentRun,
  Deliverable,
  DashboardStats,
  AgentRole,
  PipelineRunResult,
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
  runAgent: (data: { project_id: string; agent_role: AgentRole; input_data?: Record<string, unknown> }) =>
    request<AgentRun>("/agents/run", { method: "POST", body: JSON.stringify(data) }),
  runPipeline: (data: { project_id: string; agents?: AgentRole[] }) =>
    request<PipelineRunResult>("/agents/pipeline", { method: "POST", body: JSON.stringify(data) }),
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
};
