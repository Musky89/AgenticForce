from __future__ import annotations

import os
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from agency.agents import AGENTS, PIPELINE_ORDER
from agency.config import Settings
from agency.io import ensure_dir, load_project_state, read_yaml, slugify, write_yaml
from agency.models import ProjectMeta, ProjectState
from agency.orchestrator import read_brief, run_agent, run_pipeline

app = typer.Typer(
    name="agency",
    help="Solo-operated agentic creative agency — brief → strategy → creative → copy → QA.",
    no_args_is_help=True,
)
console = Console()

DEFAULT_WORKSPACE = Path(os.getenv("AGENCY_WORKSPACE", "agency_workspace"))


def _workspace() -> Path:
    return DEFAULT_WORKSPACE.resolve()


@app.command()
def init(
    name: str = typer.Argument(..., help="Project display name"),
    client: str = typer.Option(..., "--client", "-c", help="Client or brand name"),
    workspace: Path = typer.Option(
        DEFAULT_WORKSPACE,
        "--workspace",
        "-w",
        help="Root folder for all client projects",
    ),
) -> None:
    """Create a new project folder with brief template and metadata."""
    ws = workspace.resolve()
    slug = slugify(f"{client}-{name}")
    base = ws / slug
    if base.exists():
        console.print(f"[red]Already exists:[/red] {base}")
        raise typer.Exit(code=1)

    ensure_dir(base)
    ensure_dir(base / "artifacts")
    brief = base / "brief.md"
    brief.write_text(
        f"# Brief: {name}\n\n**Client:** {client}\n\n## Objective\n\n## Audience\n\n"
        "## Deliverables\n\n- \n\n## Tone & voice\n\n## Constraints\n\n"
        "## Deadline / timeline\n\n",
        encoding="utf-8",
    )
    meta = ProjectMeta(name=name, client=client)
    state = ProjectState(meta=meta)
    write_yaml(base / "project.yaml", state.to_dict())
    console.print(f"[green]Created[/green] {base}")
    console.print(f"Edit [bold]{brief}[/bold], then run: [bold]agency run {slug}[/bold]")


@app.command("list")
def list_projects(
    workspace: Path = typer.Option(DEFAULT_WORKSPACE, "--workspace", "-w"),
) -> None:
    """List projects under the workspace."""
    ws = workspace.resolve()
    if not ws.is_dir():
        console.print(f"No workspace at {ws} — run [bold]agency init[/bold] first.")
        raise typer.Exit(code=0)

    rows: list[tuple[str, str, str]] = []
    for d in sorted(ws.iterdir()):
        if not d.is_dir():
            continue
        py = d / "project.yaml"
        if not py.exists():
            continue
        data = read_yaml(py)
        meta = data.get("meta", {})
        rows.append((d.name, meta.get("name", ""), meta.get("client", "")))

    if not rows:
        console.print("No projects found.")
        return

    table = Table(title="Agency projects")
    table.add_column("Slug")
    table.add_column("Name")
    table.add_column("Client")
    for slug, name, client in rows:
        table.add_row(slug, name, client)
    console.print(table)


@app.command()
def status(
    project: str = typer.Argument(..., help="Project slug (folder name under workspace)"),
    workspace: Path = typer.Option(DEFAULT_WORKSPACE, "--workspace", "-w"),
) -> None:
    """Show project metadata and recent runs."""
    base = workspace.resolve() / project
    py = base / "project.yaml"
    if not py.exists():
        console.print(f"[red]Unknown project:[/red] {project}")
        raise typer.Exit(code=1)
    state = load_project_state(py)
    console.print(f"[bold]{state.meta.name}[/bold] — {state.meta.client}")
    console.print(f"Updated: {state.meta.updated_at}")
    if not state.runs:
        console.print("No runs yet.")
        return
    last = state.runs[-1]
    console.print(
        f"Last run: {last.run_id} | {last.status} | model={last.model} | "
        f"agents={', '.join(last.agents_completed) or '—'}"
    )
    if last.error:
        console.print(f"[red]{last.error}[/red]")


@app.command()
def run(
    project: str = typer.Argument(..., help="Project slug"),
    workspace: Path = typer.Option(DEFAULT_WORKSPACE, "--workspace", "-w"),
    from_agent: str | None = typer.Option(
        None,
        "--from",
        help="Resume from this agent: strategy | creative | copy | qa",
    ),
    temperature: float = typer.Option(0.7, "--temperature", "-t", min=0.0, max=2.0),
) -> None:
    """Run the full pipeline (or resume from --from) using OPENAI_API_KEY."""
    base = workspace.resolve() / project
    if not (base / "brief.md").exists():
        console.print(f"[red]Missing brief or project:[/red] {base}")
        raise typer.Exit(code=1)

    settings = Settings.load()
    console.print(f"Model: [bold]{settings.model}[/bold]")
    try:
        record = run_pipeline(base, settings, from_agent=from_agent, temperature=temperature)
    except Exception as e:
        console.print(f"[red]Run failed:[/red] {e}")
        raise typer.Exit(code=1) from e

    console.print(f"[green]OK[/green] run {record.run_id} — artifacts in {base / 'artifacts'}")


@app.command()
def agent(
    project: str = typer.Argument(..., help="Project slug"),
    agent_id: str = typer.Argument(..., help="strategy | creative | copy | qa"),
    workspace: Path = typer.Option(DEFAULT_WORKSPACE, "--workspace", "-w"),
    temperature: float = typer.Option(0.7, "--temperature", "-t", min=0.0, max=2.0),
) -> None:
    """Run a single agent (overwrites that agent's artifact)."""
    if agent_id not in AGENTS:
        console.print(f"[red]Unknown agent:[/red] {agent_id}. Choose: {', '.join(PIPELINE_ORDER)}")
        raise typer.Exit(code=1)
    base = workspace.resolve() / project
    settings = Settings.load()
    brief_path = base / "brief.md"
    if not brief_path.exists():
        console.print(f"[red]Missing brief:[/red] {brief_path}")
        raise typer.Exit(code=1)
    brief = read_brief(brief_path)
    try:
        run_agent(settings, agent_id, brief, base / "artifacts", temperature=temperature)
    except Exception as e:
        console.print(f"[red]Failed:[/red] {e}")
        raise typer.Exit(code=1) from e
    fn = AGENTS[agent_id].output_filename
    console.print(f"[green]Wrote[/green] {base / 'artifacts' / fn}")


def main() -> None:
    app()


if __name__ == "__main__":
    main()
