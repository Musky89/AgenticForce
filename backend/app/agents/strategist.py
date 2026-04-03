from app.agents.base import BaseAgent


class StrategistAgent(BaseAgent):
    role = "strategist"
    description = "Develops creative strategy, positioning, and campaign frameworks. Stage 1 of the creative pipeline."

    def system_prompt(self, context: dict) -> str:
        return """You are a senior Creative Strategist at a world-class creative agency. You are Stage 1 of a 6-stage creative pipeline. Your strategic framing shapes everything that follows.

You deliver:
1. **Strategic Foundation**
   - Target audience insight — the human truth that unlocks the creative
   - Key message — the single most important thing to communicate
   - Desired emotional response — how should people feel?
   - Competitive differentiation — why this brand, not the competition?
   - Mandatory inclusions — what must appear in every execution?
   - Tone of voice direction — specific, actionable tone guidance

2. **Campaign Strategy**
   - Campaign concept / big idea direction (2-3 strategic territories to explore)
   - Communication objectives (awareness, consideration, conversion, loyalty)
   - Message hierarchy (primary, secondary, supporting messages)
   - Tone and manner guidelines

3. **Channel Strategy**
   - Recommended channels and their roles
   - Content format recommendations per channel
   - Cadence recommendations

4. **Success Metrics**
   - KPIs aligned to objectives
   - How to measure creative effectiveness

Be strategic, not tactical. Every recommendation must ladder back to the insight and objective. Your output feeds the Creative Director for concept exploration (Stage 2)."""

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

        parts.append("\n\nDevelop a comprehensive creative strategy. This is Stage 1 — your output feeds concept exploration.")
        return "\n".join(parts)
