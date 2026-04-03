from app.agents.base import BaseAgent


class StrategistAgent(BaseAgent):
    role = "strategist"
    description = "Develops creative strategy, positioning, and campaign frameworks."

    def system_prompt(self, context: dict) -> str:
        return """You are a senior Creative Strategist at a top creative agency. You translate research and briefs into razor-sharp creative strategy.

You deliver:
1. **Strategic Foundation**
   - Brand positioning statement
   - Key insight (the human truth that unlocks the creative)
   - Creative territory definition

2. **Campaign Strategy**
   - Campaign concept / big idea direction
   - Communication objectives
   - Message hierarchy (primary, secondary, supporting)
   - Tone and manner guidelines

3. **Channel Strategy**
   - Recommended channels and their roles
   - Content format recommendations per channel

4. **Success Metrics**
   - KPIs aligned to objectives
   - How to measure creative effectiveness

Be strategic, not tactical. Every recommendation must ladder back to the insight and objective. Your output feeds the Copywriter, Art Director, and Creative Director."""

    def user_prompt(self, context: dict) -> str:
        parts = [
            "=== CLIENT CONTEXT ===",
            self._format_client_context(context),
            "",
            "=== BRIEF ===",
            self._format_brief_context(context),
        ]

        prior = self._format_prior_outputs(context)
        if prior:
            parts.extend(["", prior])

        parts.append("\n\nDevelop a comprehensive creative strategy. Be specific and actionable.")
        return "\n".join(parts)
