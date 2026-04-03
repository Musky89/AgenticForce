import time
import logging
from abc import ABC, abstractmethod
from openai import AsyncOpenAI
from app.config import get_settings

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all creative agency agents."""

    role: str = "agent"
    description: str = "A creative agency agent."

    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    @abstractmethod
    def system_prompt(self, context: dict) -> str:
        ...

    @abstractmethod
    def user_prompt(self, context: dict) -> str:
        ...

    def _format_client_context(self, context: dict) -> str:
        client = context.get("client", {})
        parts = [f"Client: {client.get('name', 'Unknown')}"]
        if client.get("industry"):
            parts.append(f"Industry: {client['industry']}")
        return "\n".join(parts)

    def _format_brand_bible(self, context: dict) -> str:
        """Format the Brand Bible into a rich context string for agent consumption."""
        bible = context.get("brand_bible", {})
        if not bible:
            return ""

        sections = []

        # Positioning
        pos_fields = [
            ("brand_essence", "Brand Essence"),
            ("positioning_statement", "Positioning"),
            ("unique_selling_proposition", "USP"),
            ("mission", "Mission"),
            ("vision", "Vision"),
            ("values", "Values"),
        ]
        pos = [f"{label}: {bible[k]}" for k, label in pos_fields if bible.get(k)]
        if pos:
            sections.append("BRAND POSITIONING\n" + "\n".join(pos))

        # Audience
        aud_fields = [("primary_audience", "Primary Audience"), ("secondary_audience", "Secondary Audience")]
        aud = [f"{label}: {bible[k]}" for k, label in aud_fields if bible.get(k)]
        if aud:
            sections.append("TARGET AUDIENCE\n" + "\n".join(aud))

        # Visual Identity
        vis = []
        if bible.get("color_palette"):
            palette = bible["color_palette"]
            vis.append(f"Color Palette: Primary {palette.get('primary', [])}, Secondary {palette.get('secondary', [])}, Accent {palette.get('accent', [])}")
        if bible.get("typography"):
            vis.append(f"Typography: {bible['typography']}")
        for k, label in [("photography_style", "Photography Style"), ("illustration_style", "Illustration Style"),
                          ("composition_rules", "Composition Rules"), ("visual_dos", "Visual Do's"),
                          ("visual_donts", "Visual Don'ts"), ("logo_usage", "Logo Usage")]:
            if bible.get(k):
                vis.append(f"{label}: {bible[k]}")
        if vis:
            sections.append("VISUAL IDENTITY\n" + "\n".join(vis))

        # Verbal Identity
        verb = []
        for k, label in [("tone_of_voice", "Tone of Voice"), ("headline_style", "Headline Style"),
                          ("copy_style", "Copy Style"), ("vocabulary_preferences", "Preferred Words"),
                          ("vocabulary_avoid", "Words to Avoid")]:
            if bible.get(k):
                verb.append(f"{label}: {bible[k]}")
        if bible.get("voice_attributes"):
            va = bible["voice_attributes"]
            verb.append(f"Voice Is: {', '.join(va.get('is', []))}")
            verb.append(f"Voice Is Not: {', '.join(va.get('is_not', []))}")
        if verb:
            sections.append("VERBAL IDENTITY\n" + "\n".join(verb))

        # Competitive
        if bible.get("differentiation"):
            sections.append(f"COMPETITIVE DIFFERENTIATION\n{bible['differentiation']}")

        return "\n\n".join(sections)

    def _format_brief_context(self, context: dict) -> str:
        brief = context.get("brief", {})
        fields = [
            ("objective", "Objective"),
            ("deliverables_description", "Deliverables"),
            ("target_audience", "Target Audience"),
            ("key_messages", "Key Messages"),
            ("tone", "Tone"),
            ("constraints", "Constraints"),
            ("inspiration", "Inspiration"),
            ("additional_context", "Additional Context"),
            ("desired_emotional_response", "Desired Emotional Response"),
            ("mandatory_inclusions", "Mandatory Inclusions"),
            ("competitive_differentiation", "Competitive Differentiation"),
        ]
        parts = [f"{label}: {brief[k]}" for k, label in fields if brief.get(k)]
        if brief.get("output_formats"):
            parts.append(f"Output Formats: {brief['output_formats']}")
        return "\n".join(parts) if parts else "No brief provided."

    def _format_prior_outputs(self, context: dict) -> str:
        prior = context.get("prior_outputs", {})
        if not prior:
            return ""
        parts = ["=== Prior Agent Outputs ==="]
        for role, output in prior.items():
            parts.append(f"\n--- {role.replace('_', ' ').title()} ---")
            if isinstance(output, dict):
                for k, v in output.items():
                    parts.append(f"{k}: {v}")
            else:
                parts.append(str(output))
        return "\n".join(parts)

    async def run(self, context: dict) -> dict:
        """Execute the agent and return structured output."""
        start = time.time()
        system = self.system_prompt(context)
        user = self.user_prompt(context)

        logger.info(f"Running {self.role} agent")

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.7,
            max_tokens=4096,
        )

        content = response.choices[0].message.content
        tokens = response.usage.total_tokens if response.usage else 0
        duration = time.time() - start

        return {
            "content": content,
            "tokens_used": tokens,
            "duration_seconds": round(duration, 2),
        }
