# Agentic creative agency

A **solo-operated**, multi-agent creative pipeline you run from the terminal. You stay the operator: you own the brief, the client relationship, and which runs go out the door. The tool chains **strategy → creative direction → copy → QA** into markdown artifacts you can edit, version, and hand off.

## What you get

- **Four specialist agents** (prompted as strategist, creative director, copywriter, QA lead).
- **Per-client project folders** with `brief.md`, `project.yaml` run history, and `artifacts/*.md`.
- **Resume-friendly runs**: rerun from any stage (`--from qa` after you tweak copy, etc.).
- **Single-agent mode** when you only want to refresh one layer.

## Setup

Requires Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
# Edit .env: set OPENAI_API_KEY (optional: AGENCY_MODEL=gpt-4o-mini)
```

## Usage

Default workspace is `./agency_workspace`. Override with `AGENCY_WORKSPACE` or `-w`.

```bash
# New client project
agency init "Spring campaign" --client "Acme"

# Edit agency_workspace/<slug>/brief.md — objective, audience, deliverables, tone, constraints

# Full pipeline
agency run <slug>

# Resume from creative onward (e.g. after editing strategy artifact)
agency run <slug> --from creative

# Regenerate only copy
agency agent <slug> copy

# List projects / check last run
agency list
agency status <slug>
```

## Artifacts

| File | Agent |
|------|--------|
| `artifacts/01_strategy.md` | Strategy |
| `artifacts/02_creative.md` | Creative direction |
| `artifacts/03_copy.md` | Copy |
| `artifacts/04_qa.md` | QA report |

You can edit any artifact and rerun downstream agents only, so the workflow stays under your control.

## CLI entry point

The console script is `agency` (see `pyproject.toml`). You can also run `python -m agency.cli`.

## License

MIT
