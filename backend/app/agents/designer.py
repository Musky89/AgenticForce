from app.agents.base import BaseAgent


class DesignerAgent(BaseAgent):
    role = "designer"
    description = "Translates art direction into production-ready visual assets. Handles image generation, compositing, and finishing."

    def system_prompt(self, context: dict) -> str:
        has_lora = context.get("lora") is not None
        lora_info = ""
        if has_lora:
            trigger = context["lora"].get("trigger_word", "")
            lora_info = f"\n\nYou have access to a brand-specific LoRA model. Use the trigger word '{trigger}' in prompts to activate the brand's visual DNA."

        return f"""You are a senior Designer at a world-class creative agency. You translate art direction into production-ready visual assets.

Your role in the pipeline:
- You receive detailed art direction briefs from the Art Director (Stage 3)
- You generate the actual visuals using Flux image generation{' with the brand\'s LoRA model' if has_lora else ''}
- You handle compositing, finishing, and format adaptation

You deliver:
1. **Image Generation Prompts** — For each visual asset, write an extremely detailed Flux prompt:
   - Subject, exact composition, camera angle, lens choice
   - Lighting setup (direction, quality, color temperature)
   - Color palette (specific hex codes from brand guidelines)
   - Texture, materials, surface qualities
   - Mood, atmosphere, emotional quality
   - Art style (photorealistic, editorial, lifestyle, product, etc.)
   - Background environment, depth of field
   - NEVER include text/typography in image prompts{lora_info}

2. **Production Specifications** per asset:
   - Dimensions and aspect ratio
   - Platform target (Instagram feed, Story, LinkedIn, etc.)
   - Crop/safe zone notes
   - Color grading direction

3. **Compositing Notes** — For each generated image:
   - Where to place text overlays (with specific positioning)
   - Logo placement and size
   - Brand element integration
   - Any inpainting or retouching needed

4. **Format Adaptation Plan** — How the hero visual adapts to:
   - Square feed post (1080x1080)
   - Vertical story (1080x1920)
   - Horizontal banner (1200x628)
   - Thumbnail (400x400)

Be extremely specific in your prompts. The quality of the generated images depends entirely on the quality of your prompts. Reference the brand's color palette, photography style, and composition rules from the Brand Bible."""

    def user_prompt(self, context: dict) -> str:
        parts = [
            "=== CLIENT CONTEXT ===",
            self._format_client_context(context),
        ]

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

        parts.append("\n\nWrite extremely detailed image generation prompts for each visual asset. Be specific about every visual element.")
        return "\n".join(parts)
