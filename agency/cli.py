from __future__ import annotations

import argparse
import json
from pathlib import Path

from pypdf import PdfReader

from .models import ClientBrief
from .pipeline import PhaseOneOrchestrator, creative_markdown, strategy_markdown
from .storage import PhaseOneStorage


def _read_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def _read_vision_doc(path: str | Path) -> str:
    p = Path(path)
    if p.suffix.lower() == ".pdf":
        reader = PdfReader(str(p))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n".join(pages).strip()
    return _read_text(p)


def run_phase_one(args: argparse.Namespace) -> None:
    vision_path = Path(args.vision_doc)
    brief_path = Path(args.client_brief)
    out_root = Path(args.out_dir)

    vision_text = _read_vision_doc(vision_path)
    brief_data = json.loads(_read_text(brief_path))
    brief = ClientBrief.from_dict(brief_data)

    orchestrator = PhaseOneOrchestrator()
    package = orchestrator.run(str(vision_path), vision_text, brief)

    storage = PhaseOneStorage(out_root)
    json_path = storage.save_package_json(package, brief.project_name)
    strategy_path = storage.save_markdown(
        brief.project_name, "strategy-output.md", strategy_markdown(package.strategy)
    )
    creative_path = storage.save_markdown(
        brief.project_name, "creative-development.md", creative_markdown(package)
    )

    print("Phase 1 package generated:")
    print(f"- {json_path}")
    print(f"- {strategy_path}")
    print(f"- {creative_path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agencyforce",
        description="AgenticForce Phase 1 generator (strategy + creative development).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    phase1 = sub.add_parser("phase1", help="Generate Phase 1 outputs from vision doc + client brief.")
    phase1.add_argument(
        "--vision-doc",
        required=True,
        help="Path to vision document (PDF or text).",
    )
    phase1.add_argument("--client-brief", required=True, help="Path to client brief JSON.")
    phase1.add_argument(
        "--out-dir",
        default="outputs",
        help="Directory where generated artifacts are written (default: outputs).",
    )
    phase1.set_defaults(func=run_phase_one)
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()

