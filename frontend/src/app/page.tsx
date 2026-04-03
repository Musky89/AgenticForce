"use client";

import { useEffect, useState } from "react";
import {
  Users,
  FolderKanban,
  Sparkles,
  Package,
  Activity,
  CheckCircle2,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { api } from "@/lib/api";
import type { DashboardStats, Project } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
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

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([api.getStats(), api.listProjects()])
      .then(([s, p]) => {
        setStats(s);
        setProjects(p);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const statCards = [
    { label: "Clients", value: stats?.total_clients, icon: Users, color: "text-blue-400" },
    { label: "Projects", value: stats?.total_projects, icon: FolderKanban, color: "text-purple-400" },
    { label: "In Progress", value: stats?.projects_in_progress, icon: Activity, color: "text-amber-400" },
    { label: "Delivered", value: stats?.projects_delivered, icon: CheckCircle2, color: "text-emerald-400" },
    { label: "Agent Runs", value: stats?.total_agent_runs, icon: Sparkles, color: "text-pink-400" },
    { label: "Deliverables", value: stats?.total_deliverables, icon: Package, color: "text-cyan-400" },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground mt-1">
          Overview of your creative agency operations
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {statCards.map((card) => (
          <Card key={card.label} className="bg-card border-border">
            <CardContent className="flex items-center gap-4 pt-6">
              {loading ? (
                <Skeleton className="h-12 w-full" />
              ) : (
                <>
                  <div
                    className={`h-12 w-12 rounded-xl bg-accent flex items-center justify-center ${card.color}`}
                  >
                    <card.icon className="h-6 w-6" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">{card.label}</p>
                    <p className="text-2xl font-bold">{card.value ?? 0}</p>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle>Recent Projects</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-14 w-full" />
              ))}
            </div>
          ) : projects.length === 0 ? (
            <p className="text-muted-foreground text-center py-8">
              No projects yet.{" "}
              <Link href="/projects" className="text-primary underline">
                Create one
              </Link>
            </p>
          ) : (
            <div className="space-y-2">
              {projects.slice(0, 10).map((project) => (
                <Link
                  key={project.id}
                  href={`/projects/${project.id}`}
                  className="flex items-center justify-between p-3 rounded-lg hover:bg-accent transition-colors"
                >
                  <div>
                    <p className="font-medium">{project.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {new Date(project.created_at).toLocaleDateString()}
                    </p>
                  </div>
                  <Badge
                    className={
                      STATUS_COLORS[project.status] || "bg-zinc-500/20 text-zinc-400"
                    }
                    variant="secondary"
                  >
                    {project.status.replace("_", " ")}
                  </Badge>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
