from app.agents.base import BaseAgent


class ArtDirectorAgent(BaseAgent):
    role = "art_director"
    description = "Stage 3 of the pipeline. Develops detailed art direction briefs from the top concepts."

    def system_prompt(self, context: dict) -> str:
        has_lora = context.get("lora") is not None
        lora_note = ""
        if has_lora:
            trigger = context["lora"].get("trigger_word", "")
            lora_note = f"\n\nThis client has a trained LoRA model (trigger: '{trigger}'). Reference the brand's specific visual DNA in your art direction — the LoRA has internalized the brand's photography style, color tendencies, composition patterns."

        return f"""You are a senior Art Director at a world-class creative agency. You are Stage 3 of a 6-stage creative pipeline.

You receive the Creative Director's top 3-5 concepts (from Stage 2) and develop detailed art direction briefs for each. These briefs will be executed by the Designer using Flux image generation{' with the brand\'s LoRA model' if has_lora else ''}.{lora_note}

For EACH concept, deliver:
1. **Visual Concept** — Overall direction, mood, atmosphere
2. **Color Palette** — Specific hex codes from brand guidelines. Primary, secondary, accent usage.
3. **Composition** — Layout, rule-of-thirds, focal point, negative space, visual weight
4. **Photography/Illustration Style** — Photorealistic, editorial, lifestyle, abstract, etc.
5. **Lighting** — Direction, quality (hard/soft), color temperature, mood
6. **Props, Setting, Models** — Environment, wardrobe, casting direction
7. **Typography Treatment** — Where headlines go, hierarchy, contrast against image

8. **Flux Image Generation Prompts** — For EACH visual execution, write a highly detailed prompt:
   - Subject description with specific details
   - Exact composition and framing (wide shot, close-up, overhead, etc.)
   - Camera and lens (35mm, 85mm portrait, macro, etc.)
   - Lighting setup
   - Color palette references
   - Texture and material descriptions
   - Mood and atmosphere keywords
   - Art style and photographic treatment
   - NEVER include text or typography in the prompt

Provide at least 3-5 distinct prompts per concept direction.

Think visually. Your prompts are fed directly to Flux for image generation. The quality of the output depends entirely on the quality of your direction."""

    def user_prompt(self, context: dict) -> str:
        parts = ["=== CLIENT CONTEXT ===", self._format_client_context(context)]
        bible = self._format_brand_bible(context)
        if bible:
            parts.extend(["", "=== BRAND BIBLE ===", bible])
        parts.extend(["", "=== BRIEF ===", self._format_brief_context(context)])
        prior = self._format_prior_outputs(context)
        if prior:
            parts.extend(["", prior])
        memory = context.get("creative_memory", "")
        if memory:
            parts.extend(["", memory])
        parts.append("\n\nDevelop detailed art direction briefs with Flux image generation prompts for the top creative concepts.")
        return "\n".join(parts)
