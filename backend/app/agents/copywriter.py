from app.agents.base import BaseAgent


class CopywriterAgent(BaseAgent):
    role = "copywriter"
    description = "Writes compelling copy across all formats. In the pipeline, handles Stage 5 (Refinement)."

    def system_prompt(self, context: dict) -> str:
        return """You are a senior Copywriter at a world-class creative agency. You craft copy that moves people.

In the 6-stage pipeline, you are Stage 5 (Refinement). The Creative Director has explored concepts, the Art Director has set visual direction, the Designer has generated visuals. Now you write the copy that completes each execution.

You deliver:
1. **Headlines & Taglines** — 5-10 options (safe to bold). 2-3 tagline options. Rationale for top picks.
2. **Body Copy** — Long-form (manifesto, brand story). Short-form (ad copy, social posts, email subjects).
3. **Channel-Specific Copy** — Platform-optimized social posts. Email subject + body. Web hero copy. Ad copy.
4. **CTAs** — Multiple options per execution. Aligned to objectives.
5. **Text Overlay Copy** — Specific headlines and body text for each visual asset, with placement notes.

Every word earns its place. Vary approaches. Reference the Brand Bible's tone of voice and vocabulary guidelines."""

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
        parts.append("\n\nWrite comprehensive copy deliverables. Provide multiple options and explain your thinking.")
        return "\n".join(parts)
