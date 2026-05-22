"""Unit tests for paper lifecycle safety gate behavior."""

from __future__ import annotations

import json
from pathlib import Path

import yaml
from typer.testing import CliRunner

from tradingchassis_ops_lab.cli import app

runner = CliRunner()


def _write_paper_spec(path: Path, *, run_id: str) -> None:
    spec = {
        "spec_version": "v1",
        "run_id": run_id,
        "mode": "paper",
        "engine": "nautilus",
        "venue": "binance",
        "instrument": "BTCUSDT",
        "strategy": {"name": "toy_mean_reversion", "version": "0.1.0"},
        "data": {"dataset": "btcusdt-sample", "fingerprint": "placeholder"},
        "risk": {"profile": "tiny"},
        "observability": {"journal": True, "metrics": False, "report": False},
    }
    path.write_text(yaml.safe_dump(spec), encoding="utf-8")


def test_paper_run_is_safely_blocked_when_kill_switch_active(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_id = "paper-safety-active"
    spec_path = tmp_path / "paper-active.yaml"
    _write_paper_spec(spec_path, run_id=run_id)

    activated = runner.invoke(
        app,
        ["kill", "activate", "--run-id", run_id, "--reason", "demo block"],
    )
    assert activated.exit_code == 0

    result = runner.invoke(app, ["run", "paper", "--spec", str(spec_path)])
    assert result.exit_code == 0
    assert "status=safety_blocked" in result.stdout

    run_dir = tmp_path / "artifacts" / "runs" / run_id
    metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
    metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
    report = (run_dir / "report.md").read_text(encoding="utf-8")
    journal = [
        json.loads(line)
        for line in (run_dir / "journal.jsonl").read_text(encoding="utf-8").splitlines()
    ]

    assert metadata["status"] == "safety_blocked"
    assert metadata["paper_execution"]["status"] == "blocked"
    assert metadata["paper_execution"]["connectivity"] == "none"
    assert metadata["safety"]["kill_switch"]["state"] == "active"
    assert metadata["safety"]["lifecycle_outcome"] == "blocked_kill_switch"

    events = [entry["event"] for entry in journal]
    assert "paper_safety_blocked" in events
    assert "paper_heartbeat" not in events

    assert "## Safety status" in report
    assert "kill_switch_state: active" in report
    assert "lifecycle_outcome: blocked_kill_switch" in report
    assert "local file-based kill switch state" in report

    assert metrics["status"] == "safety_blocked"
    assert metrics["heartbeat_count"] == 0
    assert metrics["paper_lifecycle"] == "blocked_kill_switch"


def test_paper_run_preserves_normal_path_when_kill_switch_cleared(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    run_id = "paper-safety-cleared"
    spec_path = tmp_path / "paper-cleared.yaml"
    _write_paper_spec(spec_path, run_id=run_id)

    activated = runner.invoke(
        app,
        ["kill", "activate", "--run-id", run_id, "--reason", "demo block"],
    )
    assert activated.exit_code == 0
    cleared = runner.invoke(
        app,
        ["kill", "clear", "--run-id", run_id, "--reason", "demo clear"],
    )
    assert cleared.exit_code == 0

    result = runner.invoke(app, ["run", "paper", "--spec", str(spec_path)])
    assert result.exit_code == 0
    assert "status=completed" in result.stdout

    run_dir = tmp_path / "artifacts" / "runs" / run_id
    metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
    report = (run_dir / "report.md").read_text(encoding="utf-8")
    journal = [
        json.loads(line)
        for line in (run_dir / "journal.jsonl").read_text(encoding="utf-8").splitlines()
    ]

    assert metadata["status"] == "completed"
    assert metadata["paper_execution"]["status"] == "completed"
    assert metadata["safety"]["kill_switch"]["state"] == "cleared"
    assert metadata["safety"]["lifecycle_outcome"] == "checked_continue"

    checked_events = [entry for entry in journal if entry["event"] == "paper_safety_checked"]
    assert len(checked_events) == 1
    assert checked_events[0]["kill_switch_state"] == "cleared"
    assert "paper_heartbeat" in {entry["event"] for entry in journal}
    assert "## Safety status" in report
    assert "kill_switch_state: cleared" in report


def test_paper_run_records_absent_kill_switch_state_when_no_file_exists(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    run_id = "paper-safety-absent"
    spec_path = tmp_path / "paper-absent.yaml"
    _write_paper_spec(spec_path, run_id=run_id)

    result = runner.invoke(app, ["run", "paper", "--spec", str(spec_path)])
    assert result.exit_code == 0
    assert "status=completed" in result.stdout

    run_dir = tmp_path / "artifacts" / "runs" / run_id
    metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["status"] == "completed"
    assert metadata["paper_execution"]["status"] == "completed"
    assert metadata["safety"]["kill_switch"]["state"] == "absent"
    assert metadata["safety"]["lifecycle_outcome"] == "checked_continue"


def test_metrics_export_includes_kill_switch_metric_after_paper_lifecycle(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    run_id = "paper-safety-metric"
    spec_path = tmp_path / "paper-metric.yaml"
    _write_paper_spec(spec_path, run_id=run_id)

    result = runner.invoke(app, ["run", "paper", "--spec", str(spec_path)])
    assert result.exit_code == 0

    exported = runner.invoke(
        app,
        [
            "metrics",
            "export",
            "--run-id",
            run_id,
            "--artifacts-root",
            str(tmp_path / "artifacts" / "runs"),
        ],
    )
    assert exported.exit_code == 0
    assert "tradingchassis_ops_lab_kill_switch_state{" in exported.stdout
    assert f'run_id="{run_id}",state="absent"}} 0' in exported.stdout
