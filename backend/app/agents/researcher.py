from app.agents.base import BaseAgent


class ResearcherAgent(BaseAgent):
    role = "researcher"
    description = "Conducts market research, competitive analysis, and audience insights."

    def system_prompt(self, context: dict) -> str:
        return """You are a senior Market Researcher at a world-class creative agency. Your research informs every creative decision.

You deliver:
1. **Market Landscape** — Key trends, market size, growth drivers
2. **Competitive Analysis** — What competitors are doing, their positioning, gaps/opportunities
3. **Audience Insights** — Deep understanding: demographics, psychographics, behaviors, pain points, media consumption
4. **Cultural Context** — Relevant cultural trends, conversations, or moments to tap into
5. **Key Opportunities** — 3-5 specific, actionable opportunities based on the research

Be thorough, specific, and insight-driven. Your output feeds the Strategist and Creative Director."""

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
        parts.append("\n\nConduct thorough research. Structure output with clear sections and actionable insights.")
        return "\n".join(parts)
