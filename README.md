# AgenticForce

Phase 1 implementation of a solo-operated agentic creative agency focused on:

- Strategy development
- Creative concept development
- Founder quality gating

This build intentionally excludes downstream execution layers (media buying, SEO, email ops, distribution orchestration) until the strategy + creative core is stable.

## What this ships

- Vision document ingestion (PDF or text)
- Structured client brief ingestion (JSON)
- Agent orchestration for:
  - Strategist
  - Creative Director
  - Brand Guardian (quality gate)
- Exported outputs:
  - `phase1-package.json`
  - `strategy-output.md`
  - `creative-development.md`

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Run Phase 1

```bash
agencyforce phase1 \
  --vision-doc "/home/ubuntu/.cursor/projects/workspace/uploads/agentic-force-complete-brief.pdf" \
  --client-brief "examples/client-brief.json" \
  --out-dir "outputs"
```

## Output layout

```text
outputs/
  aurelia-summer-launch/
    phase1-package.json
    strategy-output.md
    creative-development.md
```

## Client brief schema

`examples/client-brief.json`:

- `project_name`
- `client_name`
- `industry`
- `objective`
- `target_audience`
- `offer`
- `channels` (array)
- `competitors` (array)
- `brand_voice`
- `constraints` (array, optional)
- `budget_notes` (optional)
- `timeline` (optional)

## Test

```bash
pytest
```
