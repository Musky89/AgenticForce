"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Layers, Plus, Loader2 } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { LoRAModel } from "@/lib/types";

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-zinc-500/20 text-zinc-400",
  training: "bg-amber-500/20 text-amber-400",
  ready: "bg-emerald-500/20 text-emerald-400",
  failed: "bg-red-500/20 text-red-400",
};

export default function LoRAPage() {
  const params = useParams();
  const router = useRouter();
  const clientId = params.id as string;

  const [models, setModels] = useState<LoRAModel[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState({ name: "", trigger_word: "" });

  const load = useCallback(async () => {
    try { setModels(await api.listClientLoras(clientId)); } catch { /* none */ }
    finally { setLoading(false); }
  }, [clientId]);

  useEffect(() => { load(); }, [load]);

  const handleCreate = async () => {
    if (!form.name.trim()) { toast.error("Name required"); return; }
    try {
      await api.createLora({ client_id: clientId, name: form.name, trigger_word: form.trigger_word || undefined });
      toast.success("LoRA model registered");
      setDialogOpen(false); setForm({ name: "", trigger_word: "" }); load();
    } catch { toast.error("Failed to create"); }
  };

  if (loading) return <div className="space-y-4"><Skeleton className="h-10 w-64" /><Skeleton className="h-48" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()}><ArrowLeft className="h-4 w-4" /></Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2"><Layers className="h-7 w-7" /> LoRA Models</h1>
          <p className="text-muted-foreground">Brand-specific fine-tuned models — the brand&apos;s visual DNA</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger render={<Button />}><Plus className="h-4 w-4 mr-2" />Register LoRA</DialogTrigger>
          <DialogContent>
            <DialogHeader><DialogTitle>Register LoRA Model</DialogTitle></DialogHeader>
            <div className="space-y-4">
              <div><Label>Name</Label><Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Brand X Visual DNA v1" /></div>
              <div><Label>Trigger Word</Label><Input value={form.trigger_word} onChange={(e) => setForm({ ...form, trigger_word: e.target.value })} placeholder="brandx_style" /></div>
              <p className="text-xs text-muted-foreground">After registering, upload training images and set the weights URL once training is complete via fal.ai or Replicate.</p>
              <Button onClick={handleCreate} className="w-full">Register</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {models.length === 0 ? (
        <Card className="bg-card border-border"><CardContent className="flex flex-col items-center py-12"><Layers className="h-12 w-12 text-muted-foreground mb-4" /><p className="text-muted-foreground">No LoRA models yet. Register one to start training.</p></CardContent></Card>
      ) : (
        <div className="space-y-3">
          {models.map((m) => (
            <Card key={m.id} className="bg-card border-border">
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">{m.name}</CardTitle>
                  <Badge className={STATUS_COLORS[m.status] || ""}>{m.status}</Badge>
                </div>
                <CardDescription>v{m.version} &middot; {m.base_model}{m.trigger_word && ` &middot; trigger: "${m.trigger_word}"`}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="flex gap-4 text-sm text-muted-foreground">
                  {m.training_images_count && <span>{m.training_images_count} training images</span>}
                  {m.training_steps && <span>{m.training_steps} steps</span>}
                  {m.weights_url && <span className="text-emerald-400">Weights loaded</span>}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
