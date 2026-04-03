from pathlib import Path

from agency.io import load_project_state, read_yaml, save_project_state, slugify, write_yaml
from agency.models import ProjectMeta, ProjectState


def test_slugify() -> None:
    assert slugify("Acme Corp / Launch!") == "acme-corp-launch"


def test_project_state_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / "project.yaml"
    meta = ProjectMeta(name="X", client="Y")
    state = ProjectState(meta=meta)
    save_project_state(p, state)
    loaded = load_project_state(p)
    assert loaded.meta.name == "X"
    assert loaded.meta.client == "Y"


def test_write_read_yaml(tmp_path: Path) -> None:
    p = tmp_path / "a.yaml"
    write_yaml(p, {"a": 1, "b": {"c": 2}})
    assert read_yaml(p) == {"a": 1, "b": {"c": 2}}
