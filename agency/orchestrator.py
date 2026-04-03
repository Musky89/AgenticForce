from __future__ import annotations

import uuid
from pathlib import Path

from agency.agents import AGENTS, PIPELINE_ORDER, build_user_message
from agency.config import Settings
from agency.io import ensure_dir, load_project_state, save_project_state
from agency.llm import complete, get_client
from agency.models import RunRecord, utc_now_iso


def read_brief(brief_path: Path) -> str:
    if not brief_path.exists():
        raise FileNotFoundError(f"Brief not found: {brief_path}")
    return brief_path.read_text(encoding="utf-8")


def load_artifact(artifacts_dir: Path, filename: str) -> str:
    p = artifacts_dir / filename
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")


def artifact_map(artifacts_dir: Path) -> dict[str, str]:
    return {
        "strategy": load_artifact(artifacts_dir, AGENTS["strategy"].output_filename),
        "creative": load_artifact(artifacts_dir, AGENTS["creative"].output_filename),
        "copy": load_artifact(artifacts_dir, AGENTS["copy"].output_filename),
    }


def write_artifact(artifacts_dir: Path, filename: str, content: str) -> None:
    ensure_dir(artifacts_dir)
    (artifacts_dir / filename).write_text(content.strip() + "\n", encoding="utf-8")


def run_agent(
    settings: Settings,
    agent_id: str,
    brief: str,
    artifacts_dir: Path,
    *,
    temperature: float = 0.7,
) -> str:
    spec = AGENTS[agent_id]
    client = get_client(settings)
    arts = artifact_map(artifacts_dir)
    user = build_user_message(agent_id, brief, arts)

    text = complete(client, settings.model, spec.system_prompt, user, temperature=temperature)
    write_artifact(artifacts_dir, spec.output_filename, text)
    return text


def run_pipeline(
    project_dir: Path,
    settings: Settings,
    *,
    from_agent: str | None = None,
    temperature: float = 0.7,
) -> RunRecord:
    brief_path = project_dir / "brief.md"
    artifacts_dir = project_dir / "artifacts"
    state_path = project_dir / "project.yaml"

    brief = read_brief(brief_path)
    state = load_project_state(state_path)
    run_id = uuid.uuid4().hex[:12]
    record = RunRecord(
        run_id=run_id,
        started_at=utc_now_iso(),
        finished_at=None,
        model=settings.model,
        agents_completed=[],
        status="running",
    )
    state.runs.append(record)
    save_project_state(state_path, state)

    try:
        start_idx = 0
        if from_agent:
            if from_agent not in PIPELINE_ORDER:
                raise ValueError(f"Unknown agent {from_agent!r}")
            start_idx = PIPELINE_ORDER.index(from_agent)

        for agent_id in PIPELINE_ORDER[start_idx:]:
            run_agent(settings, agent_id, brief, artifacts_dir, temperature=temperature)
            record.agents_completed.append(agent_id)
            save_project_state(state_path, state)

        record.status = "ok"
        record.finished_at = utc_now_iso()
        save_project_state(state_path, state)
        return record
    except Exception as e:
        record.status = "failed"
        record.error = str(e)
        record.finished_at = utc_now_iso()
        save_project_state(state_path, state)
        raise
