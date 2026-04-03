"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Layers, Plus, Loader2, Dumbbell } from "lucide-react";
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
  const [trainDialogOpen, setTrainDialogOpen] = useState(false);
  const [trainTarget, setTrainTarget] = useState<LoRAModel | null>(null);
  const [trainForm, setTrainForm] = useState({ images_data_url: "", trigger_word: "", steps: "1500" });
  const [training, setTraining] = useState(false);

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

  const openTrainDialog = (model: LoRAModel) => {
    setTrainTarget(model);
    setTrainForm({ images_data_url: "", trigger_word: model.trigger_word || "", steps: "1500" });
    setTrainDialogOpen(true);
  };

  const handleTrain = async () => {
    if (!trainTarget) return;
    if (!trainForm.images_data_url.trim()) { toast.error("Training images URL required"); return; }
    if (!trainForm.trigger_word.trim()) { toast.error("Trigger word required"); return; }
    setTraining(true);
    try {
      await api.trainLora(trainTarget.id, {
        images_data_url: trainForm.images_data_url,
        trigger_word: trainForm.trigger_word,
        steps: parseInt(trainForm.steps) || 1500,
      });
      toast.success("Training started! Status will update when complete.");
      setTrainDialogOpen(false);
      setTrainTarget(null);
      load();
    } catch {
      toast.error("Failed to start training");
    } finally {
      setTraining(false);
    }
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
                <div className="flex items-center gap-4 text-sm text-muted-foreground">
                  <div className="flex gap-4 flex-1">
                    {m.training_images_count && <span>{m.training_images_count} training images</span>}
                    {m.training_steps && <span>{m.training_steps} steps</span>}
                    {m.weights_url && <span className="text-emerald-400">Weights loaded</span>}
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => openTrainDialog(m)}
                    disabled={m.status === "training"}
                  >
                    {m.status === "training" ? (
                      <Loader2 className="h-3.5 w-3.5 mr-1 animate-spin" />
                    ) : (
                      <Dumbbell className="h-3.5 w-3.5 mr-1" />
                    )}
                    {m.status === "training" ? "Training..." : "Train"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <Dialog open={trainDialogOpen} onOpenChange={setTrainDialogOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Train LoRA — {trainTarget?.name}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Training Images URL (ZIP)</Label>
              <Input
                value={trainForm.images_data_url}
                onChange={(e) => setTrainForm({ ...trainForm, images_data_url: e.target.value })}
                placeholder="https://storage.example.com/training-images.zip"
              />
              <p className="text-xs text-muted-foreground mt-1">URL to a ZIP archive containing training images</p>
            </div>
            <div>
              <Label>Trigger Word</Label>
              <Input
                value={trainForm.trigger_word}
                onChange={(e) => setTrainForm({ ...trainForm, trigger_word: e.target.value })}
                placeholder="brandx_style"
              />
            </div>
            <div>
              <Label>Training Steps</Label>
              <Input
                type="number"
                min="100"
                max="10000"
                value={trainForm.steps}
                onChange={(e) => setTrainForm({ ...trainForm, steps: e.target.value })}
                placeholder="1500"
              />
              <p className="text-xs text-muted-foreground mt-1">Recommended: 1000–2000 steps for most datasets</p>
            </div>
            <Button onClick={handleTrain} className="w-full" disabled={training}>
              {training && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              Start Training
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
