from __future__ import annotations

from agency.models import ClientBrief
from agency.pipeline import PhaseOneOrchestrator


def test_phase1_orchestration_outputs_expected_shapes() -> None:
    brief = ClientBrief(
        project_name="Test Project",
        client_name="Test Client",
        industry="B2B SaaS",
        objective="Increase inbound qualified leads",
        target_audience="Heads of Marketing at mid-market SaaS companies",
        offer="AI-powered creative strategy sprint",
        channels=["LinkedIn", "Email", "Website"],
        competitors=["Competitor A", "Competitor B"],
        brand_voice="Clear, practical, confident",
        constraints=["No inflated claims"],
        budget_notes="Lean pilot",
        timeline="2 weeks",
    )
    vision_text = """
    1.3 Core Principles
    - Strategy before creative
    - AI first, human where it matters
    - The Brand Bible is law
    PART TWO
    10.3 The North Star
    One founder and a fleet of agents.
    END OF BRIEF
    """
    package = PhaseOneOrchestrator().run("brief.pdf", vision_text, brief)

    assert package.vision.product_name == "Agentic Force"
    assert len(package.strategy.personas) >= 2
    assert len(package.strategy.territories) >= 3
    assert len(package.creative.concept_presentations) >= 3
    assert package.quality_gate.score > 0
    assert any(p.startswith("Strategy before creative") for p in package.vision.core_principles)
