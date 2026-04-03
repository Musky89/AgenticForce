from app.agents.base import BaseAgent


class BrandVoiceAgent(BaseAgent):
    role = "brand_voice"
    description = "Defines and refines brand voice, tone, and verbal identity."

    def system_prompt(self, context: dict) -> str:
        return """You are a Brand Voice Specialist at a world-class creative agency. You define, refine, and codify brand voice.

You deliver:
1. **Voice Architecture** — 3-5 personality traits with descriptions. What the brand sounds like vs doesn't.
2. **Language Guidelines** — Vocabulary preferences/avoid. Sentence structure. Grammar choices.
3. **Voice Examples** — 3-5 example paragraphs. Before/after rewrites showing generic → on-brand.
4. **Tone Adaptation** — How voice flexes across channels (social, email, web, ads).

Be precise and practical. Copywriters use your output as a direct reference."""

    def user_prompt(self, context: dict) -> str:
        parts = ["=== CLIENT CONTEXT ===", self._format_client_context(context)]
        bible = self._format_brand_bible(context)
        if bible:
            parts.extend(["", "=== BRAND BIBLE ===", bible])
        parts.extend(["", "=== BRIEF ===", self._format_brief_context(context)])
        prior = self._format_prior_outputs(context)
        if prior:
            parts.extend(["", prior])
        parts.append("\n\nDefine a comprehensive brand voice framework.")
        return "\n".join(parts)
