"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Inbox,
  CheckCircle2,
  RotateCcw,
  Clock,
  FileText,
  ImageIcon,
  Send,
  Eye,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { ReviewItem, ReviewQueueStats } from "@/lib/types";
import Link from "next/link";

const TYPE_ICONS: Record<string, typeof FileText> = {
  strategic_framing: FileText,
  concept_exploration: Eye,
  art_direction: Eye,
  visual: ImageIcon,
  copy: FileText,
  general: FileText,
};

const TYPE_COLORS: Record<string, string> = {
  strategic_framing: "text-blue-400",
  concept_exploration: "text-purple-400",
  art_direction: "text-pink-400",
  visual: "text-rose-400",
  refinement: "text-amber-400",
};

export default function ReviewQueuePage() {
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [stats, setStats] = useState<ReviewQueueStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [feedbackInputs, setFeedbackInputs] = useState<Record<string, string>>({});
  const [activeTab, setActiveTab] = useState("pending");

  const load = useCallback(async () => {
    try {
      const [q, s] = await Promise.all([
        api.getReviewQueue(activeTab === "all" ? undefined : activeTab),
        api.getReviewStats(),
      ]);
      setItems(q);
      setStats(s);
    } catch {
      toast.error("Failed to load review queue");
    } finally {
      setLoading(false);
    }
  }, [activeTab]);

  useEffect(() => { load(); }, [load]);

  const handleApprove = async (id: string) => {
    try {
      await api.reviewAction(id, "approved", feedbackInputs[id] || undefined);
      toast.success("Approved");
      load();
    } catch {
      toast.error("Failed to approve");
    }
  };

  const handleRevision = async (id: string) => {
    const fb = feedbackInputs[id];
    if (!fb?.trim()) {
      toast.error("Provide feedback for the revision");
      return;
    }
    try {
      await api.reviewAction(id, "revision_requested", fb);
      toast.success("Revision requested");
      setFeedbackInputs({ ...feedbackInputs, [id]: "" });
      load();
    } catch {
      toast.error("Failed to request revision");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Inbox className="h-8 w-8" /> Review Queue
          </h1>
          <p className="text-muted-foreground mt-1">
            Your daily command center — quality-gated items awaiting your judgment
          </p>
        </div>
        {stats && (
          <div className="flex gap-3">
            <div className="text-center">
              <p className="text-2xl font-bold text-amber-400">{stats.pending}</p>
              <p className="text-xs text-muted-foreground">Pending</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-emerald-400">{stats.approved}</p>
              <p className="text-xs text-muted-foreground">Approved</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-orange-400">{stats.revision_requested}</p>
              <p className="text-xs text-muted-foreground">Revisions</p>
            </div>
          </div>
        )}
      </div>

      <Tabs value={activeTab} onValueChange={(v) => { setActiveTab(v); setLoading(true); }}>
        <TabsList>
          <TabsTrigger value="pending">
            <Clock className="h-3.5 w-3.5 mr-1" /> Pending
            {stats && stats.pending > 0 && <Badge variant="secondary" className="ml-2 h-5 px-1.5 text-xs">{stats.pending}</Badge>}
          </TabsTrigger>
          <TabsTrigger value="approved"><CheckCircle2 className="h-3.5 w-3.5 mr-1" /> Approved</TabsTrigger>
          <TabsTrigger value="revision_requested"><RotateCcw className="h-3.5 w-3.5 mr-1" /> Revisions</TabsTrigger>
        </TabsList>

        <TabsContent value={activeTab} className="mt-6">
          {loading ? (
            <div className="space-y-3">{[1, 2, 3].map((i) => <Skeleton key={i} className="h-24" />)}</div>
          ) : items.length === 0 ? (
            <Card className="bg-card border-border">
              <CardContent className="flex flex-col items-center py-12">
                <Inbox className="h-12 w-12 text-muted-foreground mb-4" />
                <p className="text-muted-foreground">
                  {activeTab === "pending" ? "Review queue is clear. Nice work." : "No items in this category."}
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {items.map((item) => {
                const Icon = TYPE_ICONS[item.item_type] || FileText;
                const color = TYPE_COLORS[item.item_type] || "text-zinc-400";
                return (
                  <Card key={item.id} className="bg-card border-border">
                    <CardContent className="flex items-start gap-4 pt-5">
                      <div className={`h-10 w-10 rounded-lg bg-accent flex items-center justify-center flex-shrink-0 ${color}`}>
                        <Icon className="h-5 w-5" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <p className="font-semibold text-sm">{item.title}</p>
                          <Badge variant="secondary" className="text-xs">{item.item_type.replace("_", " ")}</Badge>
                          {item.quality_score !== null && (
                            <Badge className={item.quality_score >= 7 ? "bg-emerald-500/20 text-emerald-400" : "bg-amber-500/20 text-amber-400"}>
                              {item.quality_score}/10
                            </Badge>
                          )}
                        </div>
                        <p className="text-xs text-muted-foreground mb-2">
                          {new Date(item.created_at).toLocaleDateString()} &middot;{" "}
                          <Link href={`/projects/${item.project_id}`} className="hover:text-primary underline">
                            View Project
                          </Link>
                        </p>
                        {item.feedback && (
                          <p className="text-sm text-muted-foreground bg-accent p-2 rounded mb-2">{item.feedback}</p>
                        )}
                        {item.status === "pending" && (
                          <div className="flex gap-2 mt-2">
                            <Input
                              placeholder="Feedback (optional for approve, required for revision)..."
                              value={feedbackInputs[item.id] || ""}
                              onChange={(e) => setFeedbackInputs({ ...feedbackInputs, [item.id]: e.target.value })}
                              className="flex-1 text-sm"
                            />
                            <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700" onClick={() => handleApprove(item.id)}>
                              <CheckCircle2 className="h-3.5 w-3.5 mr-1" /> Approve
                            </Button>
                            <Button size="sm" variant="outline" className="text-orange-400" onClick={() => handleRevision(item.id)}>
                              <RotateCcw className="h-3.5 w-3.5 mr-1" /> Revise
                            </Button>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
