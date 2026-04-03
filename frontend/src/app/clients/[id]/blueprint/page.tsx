"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Settings2, Loader2, Save } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { ServiceBlueprint, BlueprintTemplate } from "@/lib/types";

const TEMPLATE_LABELS: Record<BlueprintTemplate, { label: string; description: string }> = {
  social_first: { label: "Social-First Brand", description: "Fashion, lifestyle — high visual volume, LoRA model, content calendar" },
  performance: { label: "Performance Brand", description: "DTC e-commerce — paid media, A/B testing, conversion optimization" },
  content_led: { label: "Content-Led Brand", description: "B2B SaaS — blog/SEO, thought leadership, LinkedIn, email nurture" },
  new_brand: { label: "New Brand Build", description: "Full identity creation — strategy, visual identity, Brand Bible, launch" },
  traditional_media: { label: "Traditional Media", description: "Print, broadsheet, OOH — CMYK, publication templates, media booking" },
  full_service: { label: "Full-Service Retainer", description: "Everything — strategy, creative, social, paid, email, SEO, reporting" },
};

export default function BlueprintPage() {
  const params = useParams();
  const router = useRouter();
  const clientId = params.id as string;

  const [blueprint, setBlueprint] = useState<ServiceBlueprint | null>(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  const load = useCallback(async () => {
    try { setBlueprint(await api.getBlueprint(clientId)); } catch { /* none yet */ }
    finally { setLoading(false); }
  }, [clientId]);

  useEffect(() => { load(); }, [load]);

  const handleCreate = async (template: BlueprintTemplate) => {
    setCreating(true);
    try {
      await api.createBlueprint({ client_id: clientId, template_type: template });
      toast.success("Service Blueprint created");
      load();
    } catch { toast.error("Failed to create"); }
    finally { setCreating(false); }
  };

  if (loading) return <div className="space-y-4"><Skeleton className="h-10 w-64" /><Skeleton className="h-96" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()}><ArrowLeft className="h-4 w-4" /></Button>
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2"><Settings2 className="h-7 w-7" /> Service Blueprint</h1>
          <p className="text-muted-foreground">Defines what the platform does for this client</p>
        </div>
      </div>

      {blueprint ? (
        <Card className="bg-card border-border">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle>{TEMPLATE_LABELS[blueprint.template_type]?.label || blueprint.template_type}</CardTitle>
              <Badge variant="secondary">{blueprint.template_type.replace("_", " ")}</Badge>
            </div>
            <CardDescription>{TEMPLATE_LABELS[blueprint.template_type]?.description}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {blueprint.active_services && (
              <div>
                <h3 className="text-sm font-semibold mb-2">Active Services</h3>
                <div className="flex flex-wrap gap-2">
                  {(blueprint.active_services as unknown as Array<{ service: string; cadence: string }>).map((s, i) => (
                    <Badge key={i} variant="secondary" className="gap-1">
                      {s.service?.replace("_", " ")} <span className="text-muted-foreground">({s.cadence})</span>
                    </Badge>
                  ))}
                </div>
              </div>
            )}
            {blueprint.quality_thresholds && (
              <div>
                <h3 className="text-sm font-semibold mb-2">Quality Thresholds</h3>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(blueprint.quality_thresholds).map(([k, v]) => (
                    <Badge key={k} variant="outline">{k.replace("_", " ")}: {String(v)}/10</Badge>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      ) : (
        <div>
          <h2 className="text-lg font-semibold mb-4">Choose a Template</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {(Object.entries(TEMPLATE_LABELS) as [BlueprintTemplate, { label: string; description: string }][]).map(([key, { label, description }]) => (
              <button
                key={key}
                onClick={() => handleCreate(key)}
                disabled={creating}
                className="p-5 rounded-xl border border-border hover:border-primary/50 transition-all text-left disabled:opacity-50"
              >
                <p className="font-semibold">{label}</p>
                <p className="text-sm text-muted-foreground mt-1">{description}</p>
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
