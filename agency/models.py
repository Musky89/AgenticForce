from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass
class ProjectMeta:
    name: str
    client: str
    created_at: str = field(default_factory=utc_now_iso)
    updated_at: str = field(default_factory=utc_now_iso)

    def touch(self) -> None:
        self.updated_at = utc_now_iso()


@dataclass
class RunRecord:
    run_id: str
    started_at: str
    finished_at: str | None
    model: str
    agents_completed: list[str] = field(default_factory=list)
    status: str = "running"  # running | ok | failed
    error: str | None = None


@dataclass
class ProjectState:
    meta: ProjectMeta
    runs: list[RunRecord] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "meta": {
                "name": self.meta.name,
                "client": self.meta.client,
                "created_at": self.meta.created_at,
                "updated_at": self.meta.updated_at,
            },
            "runs": [
                {
                    "run_id": r.run_id,
                    "started_at": r.started_at,
                    "finished_at": r.finished_at,
                    "model": r.model,
                    "agents_completed": r.agents_completed,
                    "status": r.status,
                    "error": r.error,
                }
                for r in self.runs
            ],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProjectState:
        m = data.get("meta", {})
        meta = ProjectMeta(
            name=m.get("name", "Untitled"),
            client=m.get("client", ""),
            created_at=m.get("created_at", utc_now_iso()),
            updated_at=m.get("updated_at", utc_now_iso()),
        )
        runs: list[RunRecord] = []
        for r in data.get("runs", []):
            runs.append(
                RunRecord(
                    run_id=r["run_id"],
                    started_at=r["started_at"],
                    finished_at=r.get("finished_at"),
                    model=r.get("model", ""),
                    agents_completed=list(r.get("agents_completed", [])),
                    status=r.get("status", "ok"),
                    error=r.get("error"),
                )
            )
        return cls(meta=meta, runs=runs)


def project_paths(root: Path, slug: str) -> dict[str, Path]:
    base = root / slug
    return {
        "base": base,
        "brief": base / "brief.md",
        "project_yaml": base / "project.yaml",
        "artifacts": base / "artifacts",
    }
