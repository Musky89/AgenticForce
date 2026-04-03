"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, BookOpen, Loader2, Save, Palette, Type, Eye, MessageSquare, Swords } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { BrandBible } from "@/lib/types";

const EMPTY: Partial<BrandBible> = {
  brand_essence: "", mission: "", vision: "", values: "",
  positioning_statement: "", unique_selling_proposition: "",
  primary_audience: "", secondary_audience: "",
  photography_style: "", illustration_style: "", composition_rules: "",
  logo_usage: "", visual_dos: "", visual_donts: "",
  tone_of_voice: "", vocabulary_preferences: "", vocabulary_avoid: "",
  headline_style: "", copy_style: "", differentiation: "",
};

export default function BrandBiblePage() {
  const params = useParams();
  const router = useRouter();
  const clientId = params.id as string;

  const [bible, setBible] = useState<BrandBible | null>(null);
  const [form, setForm] = useState<Record<string, string>>(EMPTY as Record<string, string>);
  const [colorPalette, setColorPalette] = useState({ primary: "", secondary: "", accent: "" });
  const [voiceIs, setVoiceIs] = useState("");
  const [voiceIsNot, setVoiceIsNot] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    try {
      const b = await api.getBrandBible(clientId);
      setBible(b);
      const f: Record<string, string> = {};
      for (const key of Object.keys(EMPTY)) f[key] = ((b as unknown as Record<string, unknown>)[key] as string) || "";
      setForm(f);
      if (b.color_palette) {
        setColorPalette({
          primary: (b.color_palette.primary || []).join(", "),
          secondary: (b.color_palette.secondary || []).join(", "),
          accent: (b.color_palette.accent || []).join(", "),
        });
      }
      if (b.voice_attributes) {
        setVoiceIs((b.voice_attributes.is || []).join(", "));
        setVoiceIsNot((b.voice_attributes.is_not || []).join(", "));
      }
    } catch { /* No bible yet */ }
    finally { setLoading(false); }
  }, [clientId]);

  useEffect(() => { load(); }, [load]);

  const handleSave = async () => {
    setSaving(true);
    const data = {
      ...form,
      color_palette: {
        primary: colorPalette.primary.split(",").map(s => s.trim()).filter(Boolean),
        secondary: colorPalette.secondary.split(",").map(s => s.trim()).filter(Boolean),
        accent: colorPalette.accent.split(",").map(s => s.trim()).filter(Boolean),
      },
      voice_attributes: {
        is: voiceIs.split(",").map(s => s.trim()).filter(Boolean),
        is_not: voiceIsNot.split(",").map(s => s.trim()).filter(Boolean),
      },
    };
    try {
      if (bible) { await api.updateBrandBible(bible.id, data); toast.success("Brand Bible updated"); }
      else { await api.createBrandBible({ ...data, client_id: clientId }); toast.success("Brand Bible created"); }
      load();
    } catch { toast.error("Failed to save"); }
    finally { setSaving(false); }
  };

  const field = (key: string, label: string, rows = 2, placeholder = "") => (
    <div key={key}>
      <Label>{label}</Label>
      {rows === 1 ? (
        <Input value={form[key] || ""} onChange={(e) => setForm({ ...form, [key]: e.target.value })} placeholder={placeholder} />
      ) : (
        <Textarea value={form[key] || ""} onChange={(e) => setForm({ ...form, [key]: e.target.value })} rows={rows} placeholder={placeholder} />
      )}
    </div>
  );

  if (loading) return <div className="space-y-4"><Skeleton className="h-10 w-64" /><Skeleton className="h-96" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.back()}><ArrowLeft className="h-4 w-4" /></Button>
        <div className="flex-1">
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2"><BookOpen className="h-7 w-7" /> Brand Bible</h1>
          <p className="text-muted-foreground">The brand&apos;s DNA — feeds every agent automatically{bible && <Badge variant="secondary" className="ml-2">v{bible.version}</Badge>}</p>
        </div>
        <Button onClick={handleSave} disabled={saving}>{saving ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Save className="h-4 w-4 mr-2" />}Save Brand Bible</Button>
      </div>

      <Tabs defaultValue="positioning">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="positioning">Positioning</TabsTrigger>
          <TabsTrigger value="visual"><Palette className="h-3.5 w-3.5 mr-1" />Visual</TabsTrigger>
          <TabsTrigger value="verbal"><MessageSquare className="h-3.5 w-3.5 mr-1" />Verbal</TabsTrigger>
          <TabsTrigger value="audience"><Eye className="h-3.5 w-3.5 mr-1" />Audience</TabsTrigger>
          <TabsTrigger value="competitive"><Swords className="h-3.5 w-3.5 mr-1" />Competitive</TabsTrigger>
        </TabsList>

        <TabsContent value="positioning" className="mt-6">
          <Card className="bg-card border-border"><CardHeader><CardTitle>Brand Positioning</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              {field("brand_essence", "Brand Essence", 2, "The core of what the brand stands for...")}
              {field("positioning_statement", "Positioning Statement", 2, "For [audience], [brand] is the [category] that [benefit]...")}
              {field("unique_selling_proposition", "USP", 2, "The single most compelling reason to choose this brand")}
              {field("mission", "Mission", 2, "What the brand does and why")}
              {field("vision", "Vision", 2, "Where the brand is going")}
              {field("values", "Values", 2, "Core values that guide decisions")}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="visual" className="mt-6">
          <Card className="bg-card border-border"><CardHeader><CardTitle>Visual Identity</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>Color Palette — Primary (comma-separated hex codes)</Label>
                <Input value={colorPalette.primary} onChange={(e) => setColorPalette({ ...colorPalette, primary: e.target.value })} placeholder="#1a1a2e, #16213e, #0f3460" />
              </div>
              <div>
                <Label>Color Palette — Secondary</Label>
                <Input value={colorPalette.secondary} onChange={(e) => setColorPalette({ ...colorPalette, secondary: e.target.value })} placeholder="#e94560, #533483" />
              </div>
              <div>
                <Label>Color Palette — Accent</Label>
                <Input value={colorPalette.accent} onChange={(e) => setColorPalette({ ...colorPalette, accent: e.target.value })} placeholder="#f5f5f5, #ffd700" />
              </div>
              {field("photography_style", "Photography Style", 3, "Describe the photographic approach: lighting, composition, subjects...")}
              {field("illustration_style", "Illustration Style", 2, "If applicable — flat, 3D, hand-drawn, etc.")}
              {field("composition_rules", "Composition Rules", 3, "Layout principles, grid usage, visual hierarchy...")}
              {field("logo_usage", "Logo Usage", 2, "Placement rules, clear space, minimum sizes...")}
              {field("visual_dos", "Visual Do's", 3, "What to always include or emphasize visually")}
              {field("visual_donts", "Visual Don'ts", 3, "What to never do visually")}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="verbal" className="mt-6">
          <Card className="bg-card border-border"><CardHeader><CardTitle>Verbal Identity</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              {field("tone_of_voice", "Tone of Voice", 3, "How the brand sounds — specific, actionable guidance")}
              <div>
                <Label>Voice IS (comma-separated attributes)</Label>
                <Input value={voiceIs} onChange={(e) => setVoiceIs(e.target.value)} placeholder="Confident, Warm, Direct, Witty" />
              </div>
              <div>
                <Label>Voice IS NOT</Label>
                <Input value={voiceIsNot} onChange={(e) => setVoiceIsNot(e.target.value)} placeholder="Corporate, Aggressive, Passive, Jargon-heavy" />
              </div>
              {field("headline_style", "Headline Style", 2, "Short and punchy? Question-led? Statement?")}
              {field("copy_style", "Copy Style", 2, "Sentence length, paragraph structure, reading level")}
              {field("vocabulary_preferences", "Preferred Vocabulary", 2, "Words and phrases to use")}
              {field("vocabulary_avoid", "Vocabulary to Avoid", 2, "Words and phrases to never use")}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="audience" className="mt-6">
          <Card className="bg-card border-border"><CardHeader><CardTitle>Target Audience</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              {field("primary_audience", "Primary Audience", 4, "Demographics, psychographics, behaviors, pain points, media consumption...")}
              {field("secondary_audience", "Secondary Audience", 3, "Additional audience segments...")}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="competitive" className="mt-6">
          <Card className="bg-card border-border"><CardHeader><CardTitle>Competitive Landscape</CardTitle></CardHeader>
            <CardContent className="space-y-4">
              {field("differentiation", "Competitive Differentiation", 4, "What makes this brand different from competitors...")}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
