from app.models.models import AgentRole
from app.agents.base import BaseAgent
from app.agents.researcher import ResearcherAgent
from app.agents.strategist import StrategistAgent
from app.agents.brand_voice import BrandVoiceAgent
from app.agents.copywriter import CopywriterAgent
from app.agents.art_director import ArtDirectorAgent
from app.agents.creative_director import CreativeDirectorAgent

AGENT_REGISTRY: dict[AgentRole, type[BaseAgent]] = {
    AgentRole.RESEARCHER: ResearcherAgent,
    AgentRole.STRATEGIST: StrategistAgent,
    AgentRole.BRAND_VOICE: BrandVoiceAgent,
    AgentRole.COPYWRITER: CopywriterAgent,
    AgentRole.ART_DIRECTOR: ArtDirectorAgent,
    AgentRole.CREATIVE_DIRECTOR: CreativeDirectorAgent,
}


def get_agent(role: AgentRole) -> BaseAgent:
    agent_cls = AGENT_REGISTRY.get(role)
    if not agent_cls:
        raise ValueError(f"No agent registered for role: {role}")
    return agent_cls()
