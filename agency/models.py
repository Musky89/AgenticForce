from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(slots=True)
class VisionBlueprint:
    product_name: str
    north_star: str
    core_principles: list[str]
    phase_one_focus: list[str]
    strategy_outputs: list[str]
    creative_outputs: list[str]
    pipeline_stages: list[str]
    quality_dimensions: list[str]
    source_path: str
    extracted_at: str = field(default_factory=utc_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ClientBrief:
    project_name: str
    client_name: str
    industry: str
    objective: str
    target_audience: str
    offer: str
    channels: list[str]
    competitors: list[str]
    brand_voice: str
    constraints: list[str] = field(default_factory=list)
    budget_notes: str = ""
    timeline: str = ""

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ClientBrief":
        return cls(
            project_name=str(data["project_name"]).strip(),
            client_name=str(data["client_name"]).strip(),
            industry=str(data["industry"]).strip(),
            objective=str(data["objective"]).strip(),
            target_audience=str(data["target_audience"]).strip(),
            offer=str(data["offer"]).strip(),
            channels=[str(ch).strip() for ch in data.get("channels", []) if str(ch).strip()],
            competitors=[str(c).strip() for c in data.get("competitors", []) if str(c).strip()],
            brand_voice=str(data.get("brand_voice", "clear, confident, useful")).strip(),
            constraints=[str(c).strip() for c in data.get("constraints", []) if str(c).strip()],
            budget_notes=str(data.get("budget_notes", "")).strip(),
            timeline=str(data.get("timeline", "")).strip(),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Persona:
    name: str
    role: str
    pains: list[str]
    motivations: list[str]
    decision_triggers: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class StrategicTerritory:
    name: str
    insight: str
    proposition: str
    emotional_outcome: str
    proof_points: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class StrategyOutput:
    positioning_statement: str
    messaging_pillars: list[str]
    competitor_gaps: list[str]
    personas: list[Persona]
    territories: list[StrategicTerritory]
    campaign_brief: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "positioning_statement": self.positioning_statement,
            "messaging_pillars": self.messaging_pillars,
            "competitor_gaps": self.competitor_gaps,
            "personas": [p.to_dict() for p in self.personas],
            "territories": [t.to_dict() for t in self.territories],
            "campaign_brief": self.campaign_brief,
        }


@dataclass(slots=True)
class CreativeRoute:
    route_name: str
    strategic_territory: str
    big_idea: str
    taglines: list[str]
    visual_direction: list[str]
    copy_direction: list[str]
    channel_expressions: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class CreativeOutput:
    concept_presentations: list[CreativeRoute]
    moodboard_prompts: list[str]
    art_direction_notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "concept_presentations": [c.to_dict() for c in self.concept_presentations],
            "moodboard_prompts": self.moodboard_prompts,
            "art_direction_notes": self.art_direction_notes,
        }


@dataclass(slots=True)
class QualityGateReport:
    approved: bool
    score: float
    checks: dict[str, float]
    strengths: list[str]
    issues: list[str]
    next_actions: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class PhaseOnePackage:
    generated_at: str
    vision: VisionBlueprint
    brief: ClientBrief
    strategy: StrategyOutput
    creative: CreativeOutput
    quality_gate: QualityGateReport

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "vision": self.vision.to_dict(),
            "brief": self.brief.to_dict(),
            "strategy": self.strategy.to_dict(),
            "creative": self.creative.to_dict(),
            "quality_gate": self.quality_gate.to_dict(),
        }

