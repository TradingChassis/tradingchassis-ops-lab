"""Lightweight package and CLI entrypoint integration checks."""

from __future__ import annotations

import importlib
import tomllib
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_tradingchassis_ops_lab_package_imports() -> None:
    package = importlib.import_module("tradingchassis_ops_lab")
    assert package.__name__ == "tradingchassis_ops_lab"


def test_tradingchassis_ops_lab_cli_imports() -> None:
    cli = importlib.import_module("tradingchassis_ops_lab.cli")
    assert hasattr(cli, "app")


def test_pyproject_script_entrypoint_uses_tradingchassis_ops_lab() -> None:
    pyproject = tomllib.loads((_repo_root() / "pyproject.toml").read_text(encoding="utf-8"))
    scripts = pyproject.get("project", {}).get("scripts", {})
    assert scripts.get("tc") == "tradingchassis_ops_lab.cli:app"
