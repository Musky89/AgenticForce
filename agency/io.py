from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from agency.models import ProjectState


def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[-\s]+", "-", s).strip("-")
    return s or "project"


def read_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    raw = path.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)
    return data if isinstance(data, dict) else {}


def write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8")


def load_project_state(path: Path) -> ProjectState:
    return ProjectState.from_dict(read_yaml(path))


def save_project_state(path: Path, state: ProjectState) -> None:
    state.meta.touch()
    write_yaml(path, state.to_dict())


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)
