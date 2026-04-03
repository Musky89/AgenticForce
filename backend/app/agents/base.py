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
        """Return the system prompt for this agent given the project context."""
        ...

    @abstractmethod
    def user_prompt(self, context: dict) -> str:
        """Return the user prompt for this agent given the project context."""
        ...

    def _format_client_context(self, context: dict) -> str:
        client = context.get("client", {})
        parts = [f"Client: {client.get('name', 'Unknown')}"]
        if client.get("industry"):
            parts.append(f"Industry: {client['industry']}")
        if client.get("brand_guidelines"):
            parts.append(f"Brand Guidelines: {client['brand_guidelines']}")
        if client.get("tone_keywords"):
            parts.append(f"Tone Keywords: {client['tone_keywords']}")
        if client.get("target_audience"):
            parts.append(f"Target Audience: {client['target_audience']}")
        return "\n".join(parts)

    def _format_brief_context(self, context: dict) -> str:
        brief = context.get("brief", {})
        parts = [f"Objective: {brief.get('objective', 'Not specified')}"]
        if brief.get("deliverables_description"):
            parts.append(f"Deliverables: {brief['deliverables_description']}")
        if brief.get("target_audience"):
            parts.append(f"Target Audience: {brief['target_audience']}")
        if brief.get("key_messages"):
            parts.append(f"Key Messages: {brief['key_messages']}")
        if brief.get("tone"):
            parts.append(f"Tone: {brief['tone']}")
        if brief.get("constraints"):
            parts.append(f"Constraints: {brief['constraints']}")
        if brief.get("inspiration"):
            parts.append(f"Inspiration: {brief['inspiration']}")
        if brief.get("additional_context"):
            parts.append(f"Additional Context: {brief['additional_context']}")
        return "\n".join(parts)

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
