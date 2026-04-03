"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Brain, Lightbulb, BarChart3, Globe2, Sparkles, Plus, Trash2, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { CreativeMemoryEntry } from "@/lib/types";

function scoreColor(score: number | null): string {
  if (score === null) return "text-muted-foreground";
  if (score >= 8) return "text-emerald-400";
  if (score >= 6) return "text-amber-400";
  return "text-red-400";
}

function scoreBg(score: number | null): string {
  if (score === null) return "bg-muted/50";
  if (score >= 8) return "bg-emerald-500/10";
  if (score >= 6) return "bg-amber-500/10";
  return "bg-red-500/10";
}

function MemoryCard({ entry, onDelete }: { entry: CreativeMemoryEntry; onDelete: () => void }) {
  return (
    <Card className="bg-card border-border hover:border-primary/30 transition-colors">
      <CardContent className="pt-4 space-y-3">
        <div className="flex items-start justify-between gap-3">
          <p className="text-sm leading-relaxed flex-1 line-clamp-3">{entry.content}</p>
          <Button variant="ghost" size="icon" className="h-7 w-7 shrink-0 text-muted-foreground hover:text-destructive" onClick={onDelete}>
            <Trash2 className="h-3.5 w-3.5" />
          </Button>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <span className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full ${scoreBg(entry.effectiveness_score)} ${scoreColor(entry.effectiveness_score)}`}>
            {entry.effectiveness_score !== null ? `${entry.effectiveness_score}/10` : "Unscored"}
          </span>
          {entry.category && (
            <Badge variant="outline" className="text-xs">{entry.category}</Badge>
          )}
          <span className="text-xs text-muted-foreground ml-auto">
            Used {entry.times_used}x
          </span>
        </div>
        <p className="text-xs text-muted-foreground">
          {new Date(entry.created_at).toLocaleDateString()}
        </p>
      </CardContent>
    </Card>
  );
}

export default function CreativeMemoryPage() {
  const params = useParams();
  const router = useRouter();
  const clientId = params.id as string;

  const [entries, setEntries] = useState<CreativeMemoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [insights, setInsights] = useState<{ insights: string[]; patterns: string[] } | null>(null);
  const [insightsLoading, setInsightsLoading] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ memory_type: "effective_prompt", content: "", category: "", effectiveness_score: "" });

  const load = useCallback(async () => {
    try {
      setEntries(await api.listMemories(clientId));
    } catch {
      toast.error("Failed to load creative memory");
    } finally {
      setLoading(false);
    }
  }, [clientId]);

  useEffect(() => { load(); }, [load]);

  const loadInsights = async () => {
    if (insights) return;
    setInsightsLoading(true);
    try {
      setInsights(await api.getClientInsights(clientId));
    } catch {
      toast.error("Failed to load insights");
    } finally {
      setInsightsLoading(false);
    }
  };

  const handleCreate = async () => {
    if (!form.content.trim()) { toast.error("Content required"); return; }
    setCreating(true);
    try {
      await api.createMemory({
        client_id: clientId,
        memory_type: form.memory_type,
        content: form.content,
        category: form.category || undefined,
        effectiveness_score: form.effectiveness_score ? parseFloat(form.effectiveness_score) : undefined,
      });
      toast.success("Memory entry added");
      setDialogOpen(false);
      setForm({ memory_type: "effective_prompt", content: "", category: "", effectiveness_score: "" });
      load();
    } catch {
      toast.error("Failed to create entry");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await api.deleteMemory(id);
      toast.success("Entry deleted");
      load();
    } catch {
      toast.error("Failed to delete");
    }
  };

  const filterByType = (type: string) => entries.filter((e) => e.memory_type === type);

  if (loading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-96" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()}>
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Brain className="h-7 w-7" /> Creative Memory
          </h1>
          <p className="text-muted-foreground">
            What works for this client — learned from every campaign
          </p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger render={<Button />}>
            <Plus className="h-4 w-4 mr-2" />Add Entry
          </DialogTrigger>
          <DialogContent className="max-w-lg">
            <DialogHeader>
              <DialogTitle>Add Memory Entry</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>Type</Label>
                <select
                  className="flex h-8 w-full rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm transition-colors focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 dark:bg-input/30"
                  value={form.memory_type}
                  onChange={(e) => setForm({ ...form, memory_type: e.target.value })}
                >
                  <option value="effective_prompt">Effective Prompt</option>
                  <option value="style_insight">Style Insight</option>
                  <option value="performance_data">Performance Data</option>
                  <option value="cross_client_pattern">Cross-Client Pattern</option>
                </select>
              </div>
              <div>
                <Label>Content</Label>
                <Textarea
                  value={form.content}
                  onChange={(e) => setForm({ ...form, content: e.target.value })}
                  rows={3}
                  placeholder="Describe the prompt, insight, or pattern..."
                />
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <Label>Category</Label>
                  <Input
                    value={form.category}
                    onChange={(e) => setForm({ ...form, category: e.target.value })}
                    placeholder="e.g. social, email"
                  />
                </div>
                <div>
                  <Label>Effectiveness (1–10)</Label>
                  <Input
                    type="number"
                    min="1"
                    max="10"
                    step="0.1"
                    value={form.effectiveness_score}
                    onChange={(e) => setForm({ ...form, effectiveness_score: e.target.value })}
                    placeholder="8.5"
                  />
                </div>
              </div>
              <Button onClick={handleCreate} className="w-full" disabled={creating}>
                {creating && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                Add Entry
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      <Tabs defaultValue="effective_prompts">
        <TabsList>
          <TabsTrigger value="effective_prompts">
            <Sparkles className="h-3.5 w-3.5 mr-1" />Effective Prompts
          </TabsTrigger>
          <TabsTrigger value="style_insights">
            <Lightbulb className="h-3.5 w-3.5 mr-1" />Style Insights
          </TabsTrigger>
          <TabsTrigger value="performance">
            <BarChart3 className="h-3.5 w-3.5 mr-1" />Performance
          </TabsTrigger>
          <TabsTrigger value="cross_client" onClick={loadInsights}>
            <Globe2 className="h-3.5 w-3.5 mr-1" />Cross-Client
          </TabsTrigger>
        </TabsList>

        <TabsContent value="effective_prompts" className="mt-6">
          <MemorySection
            entries={filterByType("effective_prompt")}
            emptyIcon={<Sparkles className="h-12 w-12 text-muted-foreground mb-4" />}
            emptyText="No effective prompts recorded yet. Add prompts that have worked well."
            onDelete={handleDelete}
          />
        </TabsContent>

        <TabsContent value="style_insights" className="mt-6">
          <MemorySection
            entries={filterByType("style_insight")}
            emptyIcon={<Lightbulb className="h-12 w-12 text-muted-foreground mb-4" />}
            emptyText="No style insights yet. Insights about visual and copy approaches will appear here."
            onDelete={handleDelete}
          />
        </TabsContent>

        <TabsContent value="performance" className="mt-6">
          <MemorySection
            entries={filterByType("performance_data")}
            emptyIcon={<BarChart3 className="h-12 w-12 text-muted-foreground mb-4" />}
            emptyText="No performance data yet. Engagement metrics linked to creative attributes will appear here."
            onDelete={handleDelete}
          />
        </TabsContent>

        <TabsContent value="cross_client" className="mt-6">
          <div className="space-y-6">
            {insightsLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : insights ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <Card className="bg-card border-border">
                  <CardHeader>
                    <CardTitle className="text-base flex items-center gap-2">
                      <Lightbulb className="h-4 w-4" />Insights
                    </CardTitle>
                    <CardDescription>AI-derived patterns from this client&apos;s data</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {insights.insights.length > 0 ? (
                      <ul className="space-y-2">
                        {insights.insights.map((ins, i) => (
                          <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                            <span className="text-primary mt-0.5">•</span>{ins}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-sm text-muted-foreground">No insights available yet.</p>
                    )}
                  </CardContent>
                </Card>
                <Card className="bg-card border-border">
                  <CardHeader>
                    <CardTitle className="text-base flex items-center gap-2">
                      <Globe2 className="h-4 w-4" />Industry Patterns
                    </CardTitle>
                    <CardDescription>Cross-client learnings from similar brands</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {insights.patterns.length > 0 ? (
                      <ul className="space-y-2">
                        {insights.patterns.map((pat, i) => (
                          <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                            <span className="text-primary mt-0.5">•</span>{pat}
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-sm text-muted-foreground">No cross-client patterns found yet.</p>
                    )}
                  </CardContent>
                </Card>
              </div>
            ) : (
              <Card className="bg-card border-border">
                <CardContent className="flex flex-col items-center py-12">
                  <Globe2 className="h-12 w-12 text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">Click this tab to load industry-level cross-client insights.</p>
                </CardContent>
              </Card>
            )}

            <MemorySection
              entries={filterByType("cross_client_pattern")}
              emptyIcon={null}
              emptyText=""
              onDelete={handleDelete}
            />
          </div>
        </TabsContent>
      </Tabs>
    </div>
  );
}

function MemorySection({
  entries,
  emptyIcon,
  emptyText,
  onDelete,
}: {
  entries: CreativeMemoryEntry[];
  emptyIcon: React.ReactNode;
  emptyText: string;
  onDelete: (id: string) => void;
}) {
  if (entries.length === 0 && emptyText) {
    return (
      <Card className="bg-card border-border">
        <CardContent className="flex flex-col items-center py-12">
          {emptyIcon}
          <p className="text-muted-foreground">{emptyText}</p>
        </CardContent>
      </Card>
    );
  }

  if (entries.length === 0) return null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {entries.map((entry) => (
        <MemoryCard key={entry.id} entry={entry} onDelete={() => onDelete(entry.id)} />
      ))}
    </div>
  );
}
