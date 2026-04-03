"use client";

import { useEffect, useState, useCallback } from "react";
import { Plus, Pencil, Trash2, Globe, Building2, Users } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
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

const EMPTY_FORM = {
  name: "",
  industry: "",
  website: "",
  brand_guidelines: "",
  tone_keywords: "",
  target_audience: "",
  notes: "",
};

export default function ClientsPage() {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState(EMPTY_FORM);

  const loadClients = useCallback(async () => {
    try {
      const data = await api.listClients();
      setClients(data);
    } catch {
      toast.error("Failed to load clients");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadClients();
  }, [loadClients]);

  const handleSubmit = async () => {
    if (!form.name.trim()) {
      toast.error("Client name is required");
      return;
    }
    try {
      if (editingId) {
        await api.updateClient(editingId, form);
        toast.success("Client updated");
      } else {
        await api.createClient(form);
        toast.success("Client created");
      }
      setDialogOpen(false);
      setEditingId(null);
      setForm(EMPTY_FORM);
      loadClients();
    } catch {
      toast.error("Failed to save client");
    }
  };

  const handleEdit = (client: Client) => {
    setEditingId(client.id);
    setForm({
      name: client.name,
      industry: client.industry || "",
      website: client.website || "",
      brand_guidelines: client.brand_guidelines || "",
      tone_keywords: client.tone_keywords || "",
      target_audience: client.target_audience || "",
      notes: client.notes || "",
    });
    setDialogOpen(true);
  };

  const handleDelete = async (id: string) => {
    try {
      await api.deleteClient(id);
      toast.success("Client deleted");
      loadClients();
    } catch {
      toast.error("Failed to delete client");
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Clients</h1>
          <p className="text-muted-foreground mt-1">
            Manage your client portfolio
          </p>
        </div>
        <Dialog
          open={dialogOpen}
          onOpenChange={(open) => {
            setDialogOpen(open);
            if (!open) {
              setEditingId(null);
              setForm(EMPTY_FORM);
            }
          }}
        >
          <DialogTrigger render={<Button />}>
            <Plus className="h-4 w-4 mr-2" />
            New Client
          </DialogTrigger>
          <DialogContent className="max-w-lg max-h-[85vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>
                {editingId ? "Edit Client" : "New Client"}
              </DialogTitle>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <Label>Name *</Label>
                <Input
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  placeholder="Acme Corp"
                />
              </div>
              <div>
                <Label>Industry</Label>
                <Input
                  value={form.industry}
                  onChange={(e) =>
                    setForm({ ...form, industry: e.target.value })
                  }
                  placeholder="Technology, Fashion, etc."
                />
              </div>
              <div>
                <Label>Website</Label>
                <Input
                  value={form.website}
                  onChange={(e) =>
                    setForm({ ...form, website: e.target.value })
                  }
                  placeholder="https://example.com"
                />
              </div>
              <div>
                <Label>Brand Guidelines</Label>
                <Textarea
                  value={form.brand_guidelines}
                  onChange={(e) =>
                    setForm({ ...form, brand_guidelines: e.target.value })
                  }
                  placeholder="Brand colors, fonts, do's and don'ts..."
                  rows={3}
                />
              </div>
              <div>
                <Label>Tone Keywords</Label>
                <Input
                  value={form.tone_keywords}
                  onChange={(e) =>
                    setForm({ ...form, tone_keywords: e.target.value })
                  }
                  placeholder="Professional, Bold, Playful..."
                />
              </div>
              <div>
                <Label>Target Audience</Label>
                <Textarea
                  value={form.target_audience}
                  onChange={(e) =>
                    setForm({ ...form, target_audience: e.target.value })
                  }
                  placeholder="Demographics, interests, behaviors..."
                  rows={2}
                />
              </div>
              <div>
                <Label>Notes</Label>
                <Textarea
                  value={form.notes}
                  onChange={(e) => setForm({ ...form, notes: e.target.value })}
                  placeholder="Any additional notes..."
                  rows={2}
                />
              </div>
              <Button onClick={handleSubmit} className="w-full">
                {editingId ? "Save Changes" : "Create Client"}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-40" />
          ))}
        </div>
      ) : clients.length === 0 ? (
        <Card className="bg-card border-border">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Users className="h-12 w-12 text-muted-foreground mb-4" />
            <p className="text-muted-foreground">
              No clients yet. Create your first client to get started.
            </p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {clients.map((client) => (
            <Card
              key={client.id}
              className="bg-card border-border hover:border-primary/50 transition-colors"
            >
              <CardHeader className="flex flex-row items-start justify-between space-y-0 pb-2">
                <div className="flex-1 min-w-0">
                  <Link href={`/projects?client=${client.id}`}>
                    <CardTitle className="text-base truncate hover:text-primary transition-colors cursor-pointer">
                      {client.name}
                    </CardTitle>
                  </Link>
                </div>
                <div className="flex gap-1 ml-2">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8"
                    onClick={() => handleEdit(client)}
                  >
                    <Pencil className="h-3.5 w-3.5" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-destructive"
                    onClick={() => handleDelete(client.id)}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-2">
                {client.industry && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Building2 className="h-3.5 w-3.5" />
                    {client.industry}
                  </div>
                )}
                {client.website && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Globe className="h-3.5 w-3.5" />
                    <a
                      href={client.website}
                      target="_blank"
                      rel="noopener"
                      className="truncate hover:text-primary"
                    >
                      {client.website}
                    </a>
                  </div>
                )}
                {client.tone_keywords && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {client.tone_keywords.split(",").map((kw) => (
                      <span
                        key={kw}
                        className="px-2 py-0.5 text-xs rounded-full bg-accent text-accent-foreground"
                      >
                        {kw.trim()}
                      </span>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
