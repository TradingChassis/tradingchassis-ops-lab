"""CLI tests for core commands and Slice 2 workflows."""

from pathlib import Path

import yaml
from typer.testing import CliRunner

from ops_lab.cli import app

runner = CliRunner()


def test_tc_help_exits_successfully() -> None:
    """Verify the CLI help output is available."""
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0


def test_tc_version_outputs_package_version() -> None:
    """Verify the CLI version command prints the current package version."""
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.stdout


def _write_valid_spec(path: Path, run_id: str = "slice2-cli-run") -> None:
    spec = {
        "spec_version": "v1",
        "run_id": run_id,
        "mode": "backtest",
        "engine": "nautilus",
        "venue": "binance",
        "instrument": "BTCUSDT",
        "strategy": {"name": "toy_mean_reversion", "version": "0.1.0"},
        "data": {"dataset": "btcusdt-sample", "fingerprint": "placeholder"},
        "risk": {"profile": "tiny"},
        "observability": {"journal": True, "metrics": False, "report": False},
    }
    path.write_text(yaml.safe_dump(spec), encoding="utf-8")


def test_tc_spec_validate_succeeds_for_valid_spec(tmp_path: Path) -> None:
    """Validate command exits successfully for valid run spec."""
    spec_path = tmp_path / "valid.yaml"
    _write_valid_spec(spec_path)

    result = runner.invoke(app, ["spec", "validate", "--spec", str(spec_path)])
    assert result.exit_code == 0
    assert "Spec is valid" in result.stdout
    assert "slice2-cli-run" in result.stdout


def test_tc_spec_validate_fails_for_invalid_spec(tmp_path: Path) -> None:
    """Validate command exits non-zero for invalid run spec."""
    invalid_spec_path = tmp_path / "invalid.yaml"
    invalid_spec_path.write_text(
        yaml.safe_dump({"spec_version": "v1", "run_id": "x", "mode": "invalid"}),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["spec", "validate", "--spec", str(invalid_spec_path)])
    assert result.exit_code != 0
    assert "Spec validation failed" in result.stderr


def test_tc_run_init_creates_expected_artifacts(tmp_path: Path, monkeypatch) -> None:
    """Init command writes run artifacts and run metadata."""
    monkeypatch.chdir(tmp_path)
    spec_path = tmp_path / "valid.yaml"
    _write_valid_spec(spec_path, run_id="slice2-cli-run-init")

    result = runner.invoke(app, ["run", "init", "--spec", str(spec_path)])
    assert result.exit_code == 0
    assert "Initialized run artifacts at" in result.stdout
    assert "config_sha256=" in result.stdout

    run_dir = tmp_path / "artifacts" / "runs" / "slice2-cli-run-init"
    assert run_dir.is_dir()
    assert (run_dir / "run_spec.yaml").is_file()
    assert (run_dir / "metadata.json").is_file()
    assert (run_dir / "journal.jsonl").is_file()


def test_tc_run_init_fails_for_duplicate_run_id(tmp_path: Path, monkeypatch) -> None:
    """Init command fails cleanly when run artifacts already exist."""
    monkeypatch.chdir(tmp_path)
    spec_path = tmp_path / "valid.yaml"
    _write_valid_spec(spec_path, run_id="slice2-duplicate-run")

    first = runner.invoke(app, ["run", "init", "--spec", str(spec_path)])
    second = runner.invoke(app, ["run", "init", "--spec", str(spec_path)])
    assert first.exit_code == 0
    assert second.exit_code != 0
    assert "Run artifacts already exist" in second.stderr
