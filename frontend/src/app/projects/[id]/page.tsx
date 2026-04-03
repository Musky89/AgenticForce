"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Play,
  Zap,
  Clock,
  CheckCircle2,
  XCircle,
  Loader2,
  FileText,
  ThumbsUp,
  Send,
  Trash2,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type {
  ProjectDetail,
  Brief,
  AgentRun,
  AgentRole,
  Deliverable,
} from "@/lib/types";
import Link from "next/link";

const AGENT_LABELS: Record<AgentRole, string> = {
  researcher: "Researcher",
  strategist: "Strategist",
  brand_voice: "Brand Voice",
  copywriter: "Copywriter",
  art_director: "Art Director",
  creative_director: "Creative Director",
};

const AGENT_COLORS: Record<AgentRole, string> = {
  researcher: "text-cyan-400",
  strategist: "text-blue-400",
  brand_voice: "text-violet-400",
  copywriter: "text-amber-400",
  art_director: "text-pink-400",
  creative_director: "text-emerald-400",
};

const STATUS_ICON = {
  queued: Clock,
  running: Loader2,
  completed: CheckCircle2,
  failed: XCircle,
};

const PIPELINE_ORDER: AgentRole[] = [
  "researcher",
  "strategist",
  "brand_voice",
  "copywriter",
  "art_director",
  "creative_director",
];

export default function ProjectDetailPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params.id as string;

  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [runs, setRuns] = useState<AgentRun[]>([]);
  const [deliverables, setDeliverables] = useState<Deliverable[]>([]);
  const [loading, setLoading] = useState(true);
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const [singleAgentRunning, setSingleAgentRunning] = useState<AgentRole | null>(null);
  const [pipelineProgress, setPipelineProgress] = useState(0);
  const [activeTab, setActiveTab] = useState("brief");

  const load = useCallback(async () => {
    try {
      const [p, r, d] = await Promise.all([
        api.getProject(projectId),
        api.listRuns(projectId),
        api.listDeliverables(projectId),
      ]);
      setProject(p);
      setRuns(r);
      setDeliverables(d);
    } catch {
      toast.error("Failed to load project");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    load();
  }, [load]);

  const runPipeline = async () => {
    setPipelineRunning(true);
    setPipelineProgress(0);
    setActiveTab("agents");
    try {
      const interval = setInterval(() => {
        setPipelineProgress((p) => Math.min(p + 2, 95));
      }, 1000);

      const result = await api.runPipeline({ project_id: projectId });
      clearInterval(interval);
      setPipelineProgress(100);

      const failed = result.runs.filter((r) => r.status === "failed");
      if (failed.length > 0) {
        toast.warning(
          `Pipeline completed with ${failed.length} failure(s)`
        );
      } else {
        toast.success("Pipeline completed successfully!");
      }
      load();
    } catch {
      toast.error("Pipeline execution failed");
    } finally {
      setPipelineRunning(false);
      setPipelineProgress(0);
    }
  };

  const runSingleAgent = async (role: AgentRole) => {
    setSingleAgentRunning(role);
    setActiveTab("agents");
    try {
      await api.runAgent({ project_id: projectId, agent_role: role });
      toast.success(`${AGENT_LABELS[role]} completed`);
      load();
    } catch {
      toast.error(`${AGENT_LABELS[role]} failed`);
    } finally {
      setSingleAgentRunning(null);
    }
  };

  const approveDeliverable = async (id: string) => {
    try {
      await api.updateDeliverable(id, { is_approved: true });
      toast.success("Deliverable approved");
      load();
    } catch {
      toast.error("Failed to approve");
    }
  };

  const submitFeedback = async (id: string, feedback: string) => {
    try {
      await api.updateDeliverable(id, { feedback });
      toast.success("Feedback saved");
      load();
    } catch {
      toast.error("Failed to save feedback");
    }
  };

  const deleteDeliverable = async (id: string) => {
    try {
      await api.deleteDeliverable(id);
      toast.success("Deliverable deleted");
      load();
    } catch {
      toast.error("Failed to delete");
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  if (!project) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Project not found</p>
      </div>
    );
  }

  const hasBrief = !!project.brief;
  const completedRuns = runs.filter((r) => r.status === "completed");

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold tracking-tight">{project.name}</h1>
          <p className="text-muted-foreground">
            {project.client.name} &middot; Created{" "}
            {new Date(project.created_at).toLocaleDateString()}
          </p>
        </div>
        <div className="flex gap-2">
          {hasBrief && (
            <>
              <Button
                variant="outline"
                disabled={pipelineRunning || !hasBrief}
                onClick={() => {
                  const role = PIPELINE_ORDER.find(
                    (r) => !completedRuns.some((cr) => cr.agent_role === r)
                  );
                  if (role) runSingleAgent(role);
                  else toast.info("All agents have already run");
                }}
              >
                {singleAgentRunning ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Play className="h-4 w-4 mr-2" />
                )}
                Run Next Agent
              </Button>
              <Button
                disabled={pipelineRunning}
                onClick={runPipeline}
              >
                {pipelineRunning ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Zap className="h-4 w-4 mr-2" />
                )}
                Run Full Pipeline
              </Button>
            </>
          )}
        </div>
      </div>

      {pipelineRunning && (
        <div className="space-y-2">
          <div className="flex justify-between text-sm text-muted-foreground">
            <span>Pipeline executing...</span>
            <span>{Math.round(pipelineProgress)}%</span>
          </div>
          <Progress value={pipelineProgress} className="h-2" />
        </div>
      )}

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="brief">Brief</TabsTrigger>
          <TabsTrigger value="agents">
            Agents
            {completedRuns.length > 0 && (
              <Badge variant="secondary" className="ml-2 h-5 px-1.5 text-xs">
                {completedRuns.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="deliverables">
            Deliverables
            {deliverables.length > 0 && (
              <Badge variant="secondary" className="ml-2 h-5 px-1.5 text-xs">
                {deliverables.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="agents-panel">Run Agents</TabsTrigger>
        </TabsList>

        <TabsContent value="brief" className="mt-6">
          <BriefTab
            projectId={projectId}
            brief={project.brief}
            onSaved={load}
          />
        </TabsContent>

        <TabsContent value="agents" className="mt-6">
          <AgentRunsTab runs={runs} />
        </TabsContent>

        <TabsContent value="deliverables" className="mt-6">
          <DeliverablesTab
            deliverables={deliverables}
            onApprove={approveDeliverable}
            onFeedback={submitFeedback}
            onDelete={deleteDeliverable}
          />
        </TabsContent>

        <TabsContent value="agents-panel" className="mt-6">
          <AgentsPanelTab
            hasBrief={hasBrief}
            completedRuns={completedRuns}
            singleAgentRunning={singleAgentRunning}
            onRunAgent={runSingleAgent}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}

// ---- Brief Tab ----

function BriefTab({
  projectId,
  brief,
  onSaved,
}: {
  projectId: string;
  brief: Brief | null;
  onSaved: () => void;
}) {
  const [form, setForm] = useState({
    objective: brief?.objective || "",
    deliverables_description: brief?.deliverables_description || "",
    target_audience: brief?.target_audience || "",
    key_messages: brief?.key_messages || "",
    tone: brief?.tone || "",
    constraints: brief?.constraints || "",
    inspiration: brief?.inspiration || "",
    budget_notes: brief?.budget_notes || "",
    additional_context: brief?.additional_context || "",
  });
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!form.objective.trim()) {
      toast.error("Objective is required");
      return;
    }
    setSaving(true);
    try {
      if (brief) {
        await api.updateBrief(brief.id, form);
        toast.success("Brief updated");
      } else {
        await api.createBrief({ ...form, project_id: projectId });
        toast.success("Brief created");
      }
      onSaved();
    } catch {
      toast.error("Failed to save brief");
    } finally {
      setSaving(false);
    }
  };

  const fields = [
    { key: "objective", label: "Objective *", rows: 3, placeholder: "What is the goal of this project?" },
    { key: "deliverables_description", label: "Deliverables", rows: 2, placeholder: "What do you need produced?" },
    { key: "target_audience", label: "Target Audience", rows: 2, placeholder: "Who are we speaking to?" },
    { key: "key_messages", label: "Key Messages", rows: 2, placeholder: "What must be communicated?" },
    { key: "tone", label: "Tone & Manner", rows: 1, placeholder: "Bold, professional, playful..." },
    { key: "constraints", label: "Constraints", rows: 2, placeholder: "Budget limits, brand rules, legal requirements..." },
    { key: "inspiration", label: "Inspiration / References", rows: 2, placeholder: "Links, campaigns, styles you admire..." },
    { key: "budget_notes", label: "Budget Notes", rows: 1, placeholder: "Budget range or considerations" },
    { key: "additional_context", label: "Additional Context", rows: 2, placeholder: "Anything else the agents should know..." },
  ] as const;

  return (
    <Card className="bg-card border-border">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-5 w-5" />
          {brief ? "Edit Brief" : "Create Brief"}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {fields.map((field) => (
          <div key={field.key}>
            <Label>{field.label}</Label>
            {field.rows === 1 ? (
              <Input
                value={form[field.key] || ""}
                onChange={(e) =>
                  setForm({ ...form, [field.key]: e.target.value })
                }
                placeholder={field.placeholder}
              />
            ) : (
              <Textarea
                value={form[field.key] || ""}
                onChange={(e) =>
                  setForm({ ...form, [field.key]: e.target.value })
                }
                placeholder={field.placeholder}
                rows={field.rows}
              />
            )}
          </div>
        ))}
        <Button onClick={handleSave} disabled={saving} className="w-full">
          {saving ? (
            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
          ) : null}
          {brief ? "Update Brief" : "Create Brief"}
        </Button>
      </CardContent>
    </Card>
  );
}

// ---- Agent Runs Tab ----

function AgentRunsTab({ runs }: { runs: AgentRun[] }) {
  if (runs.length === 0) {
    return (
      <Card className="bg-card border-border">
        <CardContent className="flex flex-col items-center justify-center py-12">
          <Zap className="h-12 w-12 text-muted-foreground mb-4" />
          <p className="text-muted-foreground">
            No agent runs yet. Create a brief and run the pipeline.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {runs.map((run) => {
        const Icon = STATUS_ICON[run.status];
        const color = AGENT_COLORS[run.agent_role];
        return (
          <Card key={run.id} className="bg-card border-border">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className={`text-base flex items-center gap-2 ${color}`}>
                  <Icon
                    className={`h-4 w-4 ${
                      run.status === "running" ? "animate-spin" : ""
                    }`}
                  />
                  {AGENT_LABELS[run.agent_role]}
                </CardTitle>
                <div className="flex items-center gap-3 text-xs text-muted-foreground">
                  {run.tokens_used && <span>{run.tokens_used} tokens</span>}
                  {run.duration_seconds && (
                    <span>{run.duration_seconds}s</span>
                  )}
                  <Badge
                    variant="secondary"
                    className={
                      run.status === "completed"
                        ? "bg-emerald-500/20 text-emerald-400"
                        : run.status === "failed"
                          ? "bg-red-500/20 text-red-400"
                          : "bg-zinc-500/20 text-zinc-400"
                    }
                  >
                    {run.status}
                  </Badge>
                </div>
              </div>
            </CardHeader>
            {run.output_data?.content && (
              <CardContent>
                <ScrollArea className="max-h-96">
                  <div className="prose prose-invert prose-sm max-w-none whitespace-pre-wrap text-sm leading-relaxed">
                    {String(run.output_data.content)}
                  </div>
                </ScrollArea>
              </CardContent>
            )}
            {run.error_message && (
              <CardContent>
                <p className="text-sm text-red-400">{run.error_message}</p>
              </CardContent>
            )}
          </Card>
        );
      })}
    </div>
  );
}

// ---- Deliverables Tab ----

function DeliverablesTab({
  deliverables,
  onApprove,
  onFeedback,
  onDelete,
}: {
  deliverables: Deliverable[];
  onApprove: (id: string) => void;
  onFeedback: (id: string, feedback: string) => void;
  onDelete: (id: string) => void;
}) {
  const [feedbackInputs, setFeedbackInputs] = useState<Record<string, string>>({});

  if (deliverables.length === 0) {
    return (
      <Card className="bg-card border-border">
        <CardContent className="flex flex-col items-center justify-center py-12">
          <FileText className="h-12 w-12 text-muted-foreground mb-4" />
          <p className="text-muted-foreground">
            No deliverables yet. Run agents to generate creative output.
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {deliverables.map((d) => (
        <Card key={d.id} className="bg-card border-border">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2">
                {d.title}
                {d.is_approved && (
                  <Badge className="bg-emerald-500/20 text-emerald-400">
                    Approved
                  </Badge>
                )}
              </CardTitle>
              <div className="flex gap-1">
                {!d.is_approved && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-emerald-400"
                    onClick={() => onApprove(d.id)}
                  >
                    <ThumbsUp className="h-3.5 w-3.5 mr-1" />
                    Approve
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-destructive"
                  onClick={() => onDelete(d.id)}
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <ScrollArea className="max-h-80">
              <div className="prose prose-invert prose-sm max-w-none whitespace-pre-wrap text-sm leading-relaxed">
                {d.content}
              </div>
            </ScrollArea>

            <Separator />

            <div className="space-y-2">
              {d.feedback && (
                <div className="p-3 rounded-lg bg-accent text-sm">
                  <p className="text-xs text-muted-foreground mb-1">Feedback:</p>
                  {d.feedback}
                </div>
              )}
              <div className="flex gap-2">
                <Input
                  placeholder="Add feedback..."
                  value={feedbackInputs[d.id] || ""}
                  onChange={(e) =>
                    setFeedbackInputs({
                      ...feedbackInputs,
                      [d.id]: e.target.value,
                    })
                  }
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && feedbackInputs[d.id]) {
                      onFeedback(d.id, feedbackInputs[d.id]);
                      setFeedbackInputs({ ...feedbackInputs, [d.id]: "" });
                    }
                  }}
                />
                <Button
                  variant="outline"
                  size="icon"
                  onClick={() => {
                    if (feedbackInputs[d.id]) {
                      onFeedback(d.id, feedbackInputs[d.id]);
                      setFeedbackInputs({ ...feedbackInputs, [d.id]: "" });
                    }
                  }}
                >
                  <Send className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

// ---- Agents Panel Tab ----

function AgentsPanelTab({
  hasBrief,
  completedRuns,
  singleAgentRunning,
  onRunAgent,
}: {
  hasBrief: boolean;
  completedRuns: AgentRun[];
  singleAgentRunning: AgentRole | null;
  onRunAgent: (role: AgentRole) => void;
}) {
  return (
    <Card className="bg-card border-border">
      <CardHeader>
        <CardTitle>Individual Agents</CardTitle>
      </CardHeader>
      <CardContent>
        {!hasBrief ? (
          <p className="text-muted-foreground text-center py-6">
            Create a brief first before running agents.
          </p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {PIPELINE_ORDER.map((role) => {
              const hasCompleted = completedRuns.some(
                (r) => r.agent_role === role
              );
              const isRunning = singleAgentRunning === role;
              return (
                <button
                  key={role}
                  onClick={() => onRunAgent(role)}
                  disabled={isRunning || singleAgentRunning !== null}
                  className="flex items-center gap-3 p-4 rounded-xl border border-border hover:border-primary/50 transition-all text-left disabled:opacity-50"
                >
                  <div
                    className={`h-10 w-10 rounded-lg bg-accent flex items-center justify-center ${AGENT_COLORS[role]}`}
                  >
                    {isRunning ? (
                      <Loader2 className="h-5 w-5 animate-spin" />
                    ) : hasCompleted ? (
                      <CheckCircle2 className="h-5 w-5" />
                    ) : (
                      <Play className="h-5 w-5" />
                    )}
                  </div>
                  <div>
                    <p className="font-medium text-sm">
                      {AGENT_LABELS[role]}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {hasCompleted ? "Completed" : "Ready"}
                    </p>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
