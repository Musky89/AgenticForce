from __future__ import annotations

import json
from pathlib import Path

from .models import PhaseOnePackage


class PhaseOneStorage:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def project_dir(self, project_name: str) -> Path:
        safe = project_name.strip().lower().replace(" ", "-")
        path = self.root / safe
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_package_json(self, package: PhaseOnePackage, project_name: str) -> Path:
        out = self.project_dir(project_name) / "phase1-package.json"
        out.write_text(json.dumps(package.to_dict(), indent=2), encoding="utf-8")
        return out

    def save_markdown(self, project_name: str, filename: str, content: str) -> Path:
        out = self.project_dir(project_name) / filename
        out.write_text(content.rstrip() + "\n", encoding="utf-8")
        return out
