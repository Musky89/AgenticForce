from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .models import (
    ClientBrief,
    CreativeOutput,
    CreativeRoute,
    Persona,
    QualityGateReport,
    StrategicTerritory,
    StrategyOutput,
    VisionBlueprint,
)


@dataclass(slots=True)
class StrategistAgent:
    name: str = "strategist"

    def run(self, vision: VisionBlueprint, brief: ClientBrief) -> StrategyOutput:
        personas = self._build_personas(brief)
        territories = self._build_territories(brief)
        pillars = [
            f"Outcome-first positioning for {brief.target_audience}",
            "Proof-backed claims with concrete examples and case evidence",
            "Distinct voice that rejects generic AI-style creative language",
        ]
        competitor_gaps = [
            "Most competitors publish generic claims without operational proof.",
            "Few competitors connect strategy directly to channel-specific creative execution.",
            "Brand consistency is usually manual and late; quality gates should be pre-delivery.",
        ]
        campaign_brief = (
            f"Objective: {brief.objective}\n"
            f"Audience: {brief.target_audience}\n"
            f"Offer: {brief.offer}\n"
            f"Channels: {', '.join(brief.channels)}\n"
            f"Must align with principles: {', '.join(vision.core_principles[:3])}\n"
            f"Constraints: {', '.join(brief.constraints) if brief.constraints else 'None specified'}"
        )
        positioning_statement = (
            f"For {brief.target_audience}, {brief.client_name} is the {brief.industry} brand that "
            f"delivers {objective_to_phrase(brief.objective)} through strategy-led creative systems "
            "that are faster than traditional agencies and stricter on brand consistency."
        )
        return StrategyOutput(
            positioning_statement=positioning_statement,
            messaging_pillars=pillars,
            competitor_gaps=competitor_gaps,
            personas=personas,
            territories=territories,
            campaign_brief=campaign_brief,
        )

    def _build_personas(self, brief: ClientBrief) -> list[Persona]:
        return [
            Persona(
                name="Primary Buyer",
                role=f"Decision-maker in {brief.industry}",
                pains=[
                    "Inconsistent creative quality across channels",
                    "Slow agency turnaround and unclear accountability",
                    "Difficulty proving creative impact to stakeholders",
                ],
                motivations=[
                    "Faster campaign velocity without quality loss",
                    "Strategic clarity before production spend",
                    "High-confidence approval process",
                ],
                decision_triggers=[
                    "Clear strategic rationale linked to measurable outcomes",
                    "Demonstrated brand consistency framework",
                    "Production-ready deliverables with minimal revision cycles",
                ],
            ),
            Persona(
                name="Internal Champion",
                role="Marketing lead running day-to-day execution",
                pains=[
                    "Too many inputs with no coherent narrative",
                    "Limited bandwidth for repeated revision loops",
                    "Creative teams that skip strategic grounding",
                ],
                motivations=[
                    "Reusable systems and templates",
                    "Approval-ready options instead of raw explorations",
                    "Cleaner handoffs between planning and creation",
                ],
                decision_triggers=[
                    "Channel-ready concept routes",
                    "Strong voice/tone guardrails",
                    "Transparent quality checks before founder review",
                ],
            ),
        ]

    def _build_territories(self, brief: ClientBrief) -> list[StrategicTerritory]:
        return [
            StrategicTerritory(
                name="Clarity Wins",
                insight="Audiences reward brands that simplify decisions with concrete outcomes.",
                proposition=f"{brief.client_name} removes ambiguity and turns intent into shipped outcomes.",
                emotional_outcome="Confidence and momentum",
                proof_points=[
                    "Step-by-step strategic framing",
                    "Outcome-led creative rationale",
                    "Consistent cross-channel messaging architecture",
                ],
            ),
            StrategicTerritory(
                name="Proof Over Hype",
                insight="Buyers have low tolerance for abstract brand promises.",
                proposition=f"{brief.client_name} demonstrates value through evidence, not adjectives.",
                emotional_outcome="Trust and credibility",
                proof_points=[
                    "Claim-to-proof messaging pattern",
                    "Case-style narratives and practical examples",
                    "Quality-gated outputs before stakeholder review",
                ],
            ),
            StrategicTerritory(
                name="Velocity With Standards",
                insight="Speed matters only when consistency is protected.",
                proposition="Creative velocity can increase when standards are encoded into the process.",
                emotional_outcome="Relief and control",
                proof_points=[
                    "Phase-gated pipeline for strategy then creative",
                    "Reusable voice and visual rules",
                    "Founder-controlled quality sign-off",
                ],
            ),
        ]


@dataclass(slots=True)
class CreativeDirectorAgent:
    name: str = "creative_director"

    def run(self, brief: ClientBrief, strategy: StrategyOutput, routes: int = 3) -> CreativeOutput:
        selected = strategy.territories[: max(1, routes)]
        concepts: list[CreativeRoute] = []
        for idx, territory in enumerate(selected, start=1):
            concepts.append(
                CreativeRoute(
                    route_name=f"Route {idx}: {territory.name}",
                    strategic_territory=territory.name,
                    big_idea=self._big_idea(brief, territory),
                    taglines=self._taglines(brief, territory),
                    visual_direction=self._visual_direction(brief, territory),
                    copy_direction=self._copy_direction(brief, territory),
                    channel_expressions={
                        channel: self._channel_expression(channel, territory)
                        for channel in brief.channels
                    },
                )
            )

        moodboard_prompts = [
            (
                f"{brief.client_name} campaign moodboard for '{territory.name}', "
                f"brand voice: {brief.brand_voice}, emotional target: {territory.emotional_outcome}, "
                f"industry: {brief.industry}, high-end editorial composition, no generic stock look"
            )
            for territory in selected
        ]
        art_direction_notes = [
            "Lead with one dominant visual metaphor per route to avoid mixed signals.",
            "Use a restrained palette and spacing system that prioritizes message legibility.",
            "Every asset must ladder back to one strategic territory and one proof point.",
        ]
        return CreativeOutput(
            concept_presentations=concepts,
            moodboard_prompts=moodboard_prompts,
            art_direction_notes=art_direction_notes,
        )

    def _big_idea(self, brief: ClientBrief, territory: StrategicTerritory) -> str:
        return (
            f"Translate '{territory.name}' into a campaign system showing how {brief.client_name} "
            f"helps {brief.target_audience} achieve {objective_to_phrase(brief.objective)} "
            "with less friction."
        )

    def _taglines(self, brief: ClientBrief, territory: StrategicTerritory) -> list[str]:
        return [
            f"{brief.client_name}: {territory.name}, executed.",
            f"From intent to outcome, without the agency drag.",
            f"Strategy first. Creative that earns action.",
        ]

    def _visual_direction(self, brief: ClientBrief, territory: StrategicTerritory) -> list[str]:
        return [
            f"Use imagery that signals {territory.emotional_outcome.lower()} over abstract aspiration.",
            "Establish clear focal hierarchy: headline > proof element > CTA.",
            "Maintain consistent framing patterns for easier multi-channel adaptation.",
        ]

    def _copy_direction(self, brief: ClientBrief, territory: StrategicTerritory) -> list[str]:
        return [
            "Short declarative headlines, one claim per line.",
            "Support each claim with a concrete proof artifact.",
            f"Tone: {brief.brand_voice}. Avoid empty superlatives and buzzword clusters.",
        ]

    def _channel_expression(self, channel: str, territory: StrategicTerritory) -> str:
        ch = channel.lower()
        if ch in {"linkedin", "x", "twitter"}:
            return f"Thought-leadership angle anchored in '{territory.insight}' with a crisp CTA."
        if ch in {"instagram", "tiktok"}:
            return f"Visual-first storytelling that embodies '{territory.emotional_outcome}'."
        if ch in {"email"}:
            return "Narrative arc: pain -> proof -> next step, with one primary CTA."
        return "Adapt route into platform-native format while preserving proposition and proof."


@dataclass(slots=True)
class BrandGuardianAgent:
    name: str = "brand_guardian"

    def run(
        self,
        vision: VisionBlueprint,
        brief: ClientBrief,
        strategy: StrategyOutput,
        creative: CreativeOutput,
    ) -> QualityGateReport:
        checks = {
            "strategy_before_creative": 10.0 if strategy.territories else 0.0,
            "voice_consistency": 8.5 if brief.brand_voice else 4.0,
            "territory_coverage": min(10.0, len(strategy.territories) * 3.0),
            "creative_route_quality": min(10.0, len(creative.concept_presentations) * 3.0),
            "channel_readiness": 8.0 if brief.channels else 2.0,
        }
        score = sum(checks.values()) / len(checks)
        issues = []
        if len(creative.concept_presentations) < 2:
            issues.append("Less than two creative routes generated; expand exploration.")
        if len(brief.channels) < 2:
            issues.append("Single-channel brief limits strategic robustness.")
        if not brief.competitors:
            issues.append("No competitors provided; competitive framing is assumption-based.")

        approved = score >= 7.5 and not any(v < 6.0 for v in checks.values())
        strengths = [
            "Strategy and creative sequencing is preserved.",
            "Concept routes are tied to explicit strategic territories.",
            "Outputs are structured for founder review and fast iteration.",
        ]
        next_actions = (
            ["Approve and move to visual production prep in next phase."]
            if approved
            else [
                "Refine brief constraints and competitor inputs.",
                "Generate additional concept routes and retest quality gate.",
            ]
        )
        return QualityGateReport(
            approved=approved,
            score=round(score, 2),
            checks=checks,
            strengths=strengths,
            issues=issues,
            next_actions=next_actions,
        )


def format_bullets(items: Iterable[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def objective_to_phrase(objective: str) -> str:
    normalized = " ".join(objective.strip().split())
    if not normalized:
        return "deliver measurable growth"

    # Convert common imperative starters into smoother proposition phrasing.
    replacements = {
        "increase ": "increased ",
        "improve ": "improved ",
        "reduce ": "reduced ",
        "drive ": "stronger ",
        "grow ": "grown ",
        "launch ": "a successful launch of ",
    }
    lowered = normalized.lower()
    for prefix, replacement in replacements.items():
        if lowered.startswith(prefix):
            tail = normalized[len(prefix) :].strip()
            return f"{replacement}{tail}".strip()
    return normalized.lower()
