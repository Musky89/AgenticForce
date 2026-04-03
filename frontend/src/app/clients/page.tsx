"use client";

import { useEffect, useState, useCallback } from "react";
import { Plus, Pencil, Trash2, Globe, Building2, Users, BookOpen, Settings2, Layers, Brain } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
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
import type { Client } from "@/lib/types";
import Link from "next/link";

const EMPTY_FORM = { name: "", industry: "", website: "", notes: "" };

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);

  const load = useCallback(async () => {
    try { setClients(await api.listClients()); } catch { toast.error("Failed to load clients"); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleSubmit = async () => {
    if (!form.name.trim()) { toast.error("Name required"); return; }
    try {
      if (editingId) { await api.updateClient(editingId, form); toast.success("Updated"); }
      else { await api.createClient(form); toast.success("Created"); }
      setDialogOpen(false); setEditingId(null); setForm(EMPTY_FORM); load();
    } catch { toast.error("Failed to save"); }
  };

  const handleEdit = (c: Client) => {
    setEditingId(c.id);
    setForm({ name: c.name, industry: c.industry || "", website: c.website || "", notes: c.notes || "" });
    setDialogOpen(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Clients</h1>
          <p className="text-muted-foreground mt-1">Manage your client portfolio</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={(o) => { setDialogOpen(o); if (!o) { setEditingId(null); setForm(EMPTY_FORM); } }}>
          <DialogTrigger render={<Button />}>
            <Plus className="h-4 w-4 mr-2" />New Client
          </DialogTrigger>
          <DialogContent className="max-w-lg">
            <DialogHeader><DialogTitle>{editingId ? "Edit" : "New"} Client</DialogTitle></DialogHeader>
            <div className="space-y-4">
              <div><Label>Name *</Label><Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Acme Corp" /></div>
              <div><Label>Industry</Label><Input value={form.industry} onChange={(e) => setForm({ ...form, industry: e.target.value })} placeholder="Fashion, Technology..." /></div>
              <div><Label>Website</Label><Input value={form.website} onChange={(e) => setForm({ ...form, website: e.target.value })} placeholder="https://..." /></div>
              <div><Label>Notes</Label><Textarea value={form.notes} onChange={(e) => setForm({ ...form, notes: e.target.value })} rows={2} /></div>
              <Button onClick={handleSubmit} className="w-full">{editingId ? "Save" : "Create"}</Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">{[1, 2, 3].map((i) => <Skeleton key={i} className="h-48" />)}</div>
      ) : clients.length === 0 ? (
        <Card className="bg-card border-border"><CardContent className="flex flex-col items-center py-12"><Users className="h-12 w-12 text-muted-foreground mb-4" /><p className="text-muted-foreground">No clients yet.</p></CardContent></Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {clients.map((c) => (
            <Card key={c.id} className="bg-card border-border hover:border-primary/50 transition-colors">
              <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
                <Link href={`/projects?client=${c.id}`}><CardTitle className="text-base hover:text-primary transition-colors cursor-pointer">{c.name}</CardTitle></Link>
                <div className="flex gap-1 ml-2">
                  <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => handleEdit(c)}><Pencil className="h-3.5 w-3.5" /></Button>
                  <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive" onClick={async () => { await api.deleteClient(c.id); load(); }}><Trash2 className="h-3.5 w-3.5" /></Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {c.industry && <div className="flex items-center gap-2 text-sm text-muted-foreground"><Building2 className="h-3.5 w-3.5" />{c.industry}</div>}
                {c.website && <div className="flex items-center gap-2 text-sm text-muted-foreground"><Globe className="h-3.5 w-3.5" /><a href={c.website} target="_blank" rel="noopener" className="truncate hover:text-primary">{c.website}</a></div>}
                <div className="flex gap-2 pt-2 border-t border-border">
                  <Link href={`/clients/${c.id}/brand-bible`}>
                    <Badge variant="secondary" className="cursor-pointer hover:bg-accent gap-1"><BookOpen className="h-3 w-3" />Brand Bible</Badge>
                  </Link>
                  <Link href={`/clients/${c.id}/blueprint`}>
                    <Badge variant="secondary" className="cursor-pointer hover:bg-accent gap-1"><Settings2 className="h-3 w-3" />Blueprint</Badge>
                  </Link>
                  <Link href={`/clients/${c.id}/lora`}>
                    <Badge variant="secondary" className="cursor-pointer hover:bg-accent gap-1"><Layers className="h-3 w-3" />LoRA</Badge>
                  </Link>
                  <Link href={`/clients/${c.id}/memory`}>
                    <Badge variant="secondary" className="cursor-pointer hover:bg-accent gap-1"><Brain className="h-3 w-3" />Memory</Badge>
                  </Link>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
