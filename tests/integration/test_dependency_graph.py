"""Enforce the PRD dependency rules across workspace packages.

- No cycles among ``python-tools-*`` distributions.
- Nothing depends on ``python-tools-testing`` (except test extras, which are not
  declared as runtime dependencies here).
"""

from __future__ import annotations

import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

REPO_ROOT = Path(__file__).resolve().parents[2]
PACKAGES_DIR = REPO_ROOT / "packages"


def _workspace_dependencies() -> dict[str, set[str]]:
    graph: dict[str, set[str]] = {}
    for pyproject in PACKAGES_DIR.glob("*/pyproject.toml"):
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        name = data["project"]["name"]
        deps = data["project"].get("dependencies", [])
        graph[name] = {
            d.split(">")[0].split("<")[0].split("=")[0].split("~")[0].strip()
            for d in deps
            if d.startswith("python-tools-")
        }
    return graph


def test_no_dependency_cycles() -> None:
    graph = _workspace_dependencies()
    visiting: set[str] = set()
    done: set[str] = set()

    def visit(node: str, trail: list[str]) -> None:
        if node in done:
            return
        if node in visiting:
            raise AssertionError(f"dependency cycle: {' -> '.join([*trail, node])}")
        visiting.add(node)
        for dep in graph.get(node, set()):
            visit(dep, [*trail, node])
        visiting.discard(node)
        done.add(node)

    for pkg in graph:
        visit(pkg, [])


def test_nothing_depends_on_testing() -> None:
    graph = _workspace_dependencies()
    offenders = {pkg for pkg, deps in graph.items() if "python-tools-testing" in deps}
    assert offenders == set(), f"packages must not depend on testing: {offenders}"


def test_all_ten_distributions_present() -> None:
    graph = _workspace_dependencies()
    expected = {
        "python-tools-config",
        "python-tools-logging",
        "python-tools-observability",
        "python-tools-auth",
        "python-tools-fastapi",
        "python-tools-events",
        "python-tools-jobs",
        "python-tools-storage",
        "python-tools-llm",
        "python-tools-testing",
    }
    assert set(graph) == expected
