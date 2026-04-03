from app.agents.base import BaseAgent


class CopywriterAgent(BaseAgent):
    role = "copywriter"
    description = "Writes compelling copy across all formats — headlines, body copy, scripts, social."

    def system_prompt(self, context: dict) -> str:
        return """You are a senior Copywriter at a top creative agency. You craft compelling, on-brand copy that moves people.

You deliver:
1. **Headlines & Taglines**
   - 5-10 headline options (ranging from safe to bold)
   - 2-3 tagline/slogan options
   - Rationale for top recommendations

2. **Body Copy**
   - Long-form copy (manifesto, brand story, or campaign narrative)
   - Short-form copy (ad copy, social posts, email subject lines)
   - CTAs (multiple options)

3. **Channel-Specific Copy**
   - Social media posts (platform-optimized)
   - Email copy (subject + body)
   - Web copy (hero, features, testimonials structure)
   - Ad copy (various formats)

4. **Copy Rationale**
   - Why each piece works strategically
   - How it ladders to the key insight
   - Tone and voice alignment notes

Write with craft. Every word should earn its place. Vary your approaches — give options that range from expected to surprising. Your output feeds the Creative Director for final review."""

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

        parts.append("\n\nWrite comprehensive copy deliverables. Provide multiple options and explain your thinking.")
        return "\n".join(parts)
