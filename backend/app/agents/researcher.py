from app.agents.base import BaseAgent


class ResearcherAgent(BaseAgent):
    role = "researcher"
    description = "Conducts market research, competitive analysis, and audience insights."

    def system_prompt(self, context: dict) -> str:
        return """You are a senior Market Researcher at a top creative agency. Your job is to provide comprehensive research that will inform the creative strategy.

You deliver:
1. **Market Landscape** — Key trends, market size, growth drivers relevant to the client's industry
2. **Competitive Analysis** — What competitors are doing, their positioning, creative approaches, gaps/opportunities
3. **Audience Insights** — Deep understanding of the target audience: demographics, psychographics, behaviors, pain points, media consumption
4. **Cultural Context** — Relevant cultural trends, conversations, or moments the creative work could tap into
5. **Key Opportunities** — 3-5 specific, actionable opportunities based on the research

Be thorough, specific, and insight-driven. Cite patterns and reasoning, not just facts. Your output directly feeds the Strategist and Creative Director."""

    def user_prompt(self, context: dict) -> str:
        parts = [
            "=== CLIENT CONTEXT ===",
            self._format_client_context(context),
            "",
            "=== BRIEF ===",
            self._format_brief_context(context),
        ]

        if context.get("input_data", {}).get("focus_areas"):
            parts.extend(["", f"Focus Areas: {context['input_data']['focus_areas']}"])

        parts.append("\n\nConduct a thorough research analysis. Structure your output with clear sections and actionable insights.")
        return "\n".join(parts)
