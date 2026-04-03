from __future__ import annotations

from dataclasses import dataclass

from agency import prompts


@dataclass(frozen=True)
class AgentSpec:
    id: str
    title: str
    system_prompt: str
    output_filename: str


AGENTS: dict[str, AgentSpec] = {
    "strategy": AgentSpec(
        id="strategy",
        title="Strategy",
        system_prompt=prompts.STRATEGY,
        output_filename="01_strategy.md",
    ),
    "creative": AgentSpec(
        id="creative",
        title="Creative direction",
        system_prompt=prompts.CREATIVE,
        output_filename="02_creative.md",
    ),
    "copy": AgentSpec(
        id="copy",
        title="Copy",
        system_prompt=prompts.COPY,
        output_filename="03_copy.md",
    ),
    "qa": AgentSpec(
        id="qa",
        title="QA & consolidation",
        system_prompt=prompts.QA,
        output_filename="04_qa.md",
    ),
}

PIPELINE_ORDER = ("strategy", "creative", "copy", "qa")


def brief_user_block(brief: str) -> str:
    return f"""## Client brief (source of truth)

{brief.strip()}
"""


def strategy_user(brief: str) -> str:
    return brief_user_block(brief) + (
        "\nProduce: positioning summary, audience segments, key messages, "
        "channel recommendations, and success metrics."
    )


def creative_user(brief: str, strategy_md: str) -> str:
    return (
        brief_user_block(brief)
        + "\n## Prior strategy output\n\n"
        + strategy_md.strip()
        + "\n\nProduce 2–3 creative territories with rationale and example headlines/taglines."
    )


def copy_user(brief: str, strategy_md: str, creative_md: str) -> str:
    return (
        brief_user_block(brief)
        + "\n## Strategy\n\n"
        + strategy_md.strip()
        + "\n\n## Creative direction\n\n"
        + creative_md.strip()
        + "\n\nWrite the requested deliverables from the brief."
    )


def qa_user(brief: str, strategy_md: str, creative_md: str, copy_md: str) -> str:
    return (
        brief_user_block(brief)
        + "\n## Strategy\n\n"
        + strategy_md.strip()
        + "\n\n## Creative\n\n"
        + creative_md.strip()
        + "\n\n## Copy\n\n"
        + copy_md.strip()
        + "\n\nReview everything against the brief and output your QA report."
    )


def build_user_message(
    agent_id: str,
    brief: str,
    artifacts: dict[str, str],
) -> str:
    if agent_id == "strategy":
        return strategy_user(brief)
    if agent_id == "creative":
        return creative_user(brief, artifacts.get("strategy", ""))
    if agent_id == "copy":
        return copy_user(
            brief,
            artifacts.get("strategy", ""),
            artifacts.get("creative", ""),
        )
    if agent_id == "qa":
        return qa_user(
            brief,
            artifacts.get("strategy", ""),
            artifacts.get("creative", ""),
            artifacts.get("copy", ""),
        )
    raise ValueError(f"Unknown agent: {agent_id}")
