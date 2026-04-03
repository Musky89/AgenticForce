"use client";

import { useEffect, useState, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { Plus, FolderKanban } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { Client, Project } from "@/lib/types";
import Link from "next/link";

const STATUS_COLORS: Record<string, string> = {
  draft: "bg-zinc-500/20 text-zinc-400",
  briefed: "bg-blue-500/20 text-blue-400",
  in_progress: "bg-amber-500/20 text-amber-400",
  review: "bg-purple-500/20 text-purple-400",
  revision: "bg-orange-500/20 text-orange-400",
  approved: "bg-emerald-500/20 text-emerald-400",
  delivered: "bg-green-500/20 text-green-400",
};

function ProjectsContent() {
  const searchParams = useSearchParams();
  const filterClientId = searchParams.get("client");

  const [projects, setProjects] = useState<Project[]>([]);
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState({ name: "", client_id: "" });

  const load = useCallback(async () => {
    try {
      const [p, c] = await Promise.all([
        api.listProjects(filterClientId || undefined),
        api.listClients(),
      ]);
      setProjects(p);
      setClients(c);
      if (filterClientId) setForm((f) => ({ ...f, client_id: filterClientId }));
    } catch {
      toast.error("Failed to load data");
    } finally {
      setLoading(false);
    }
  }, [filterClientId]);

  useEffect(() => {
    load();
  }, [load]);

  const handleCreate = async () => {
    if (!form.name.trim() || !form.client_id) {
      toast.error("Name and client are required");
      return;
    }
    try {
      await api.createProject(form);
      toast.success("Project created");
      setDialogOpen(false);
      setForm({ name: "", client_id: filterClientId || "" });
      load();
    } catch {
      toast.error("Failed to create project");
    }
  };

  const clientName = (id: string) =>
    clients.find((c) => c.id === id)?.name || "Unknown";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Projects</h1>
          <p className="text-muted-foreground mt-1">
            {filterClientId
              ? `Projects for ${clientName(filterClientId)}`
              : "All creative projects"}
          </p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="h-4 w-4 mr-2" />
              New Project
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>New Project</DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>Client *</Label>
                <select
                  value={form.client_id}
                  onChange={(e) =>
                    setForm({ ...form, client_id: e.target.value })
                  }
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="">Select a client</option>
                  {clients.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <Label>Project Name *</Label>
                <Input
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="Q3 Brand Campaign"
                />
              </div>
              <Button onClick={handleCreate} className="w-full">
                Create Project
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-20" />
          ))}
        </div>
      ) : projects.length === 0 ? (
        <Card className="bg-card border-border">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <FolderKanban className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">
              No projects yet. Create one to start your creative workflow.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {projects.map((project) => (
            <Link key={project.id} href={`/projects/${project.id}`}>
              <Card className="bg-card border-border hover:border-primary/50 transition-colors cursor-pointer">
                <CardContent className="flex items-center justify-between py-4">
                  <div>
                    <p className="font-semibold">{project.name}</p>
                    <p className="text-sm text-muted-foreground">
                      {clientName(project.client_id)} &middot;{" "}
                      {new Date(project.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <Badge
                    className={
                      STATUS_COLORS[project.status] ||
                      "bg-zinc-500/20 text-zinc-400"
                    }
                    variant="secondary"
                  >
                    {project.status.replace("_", " ")}
                  </Badge>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

export default function ProjectsPage() {
  return (
    <Suspense
      fallback={
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-20" />
          ))}
        </div>
      }
    >
      <ProjectsContent />
    </Suspense>
  );
}
