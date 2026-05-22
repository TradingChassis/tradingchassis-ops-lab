"""CLI tests for core commands and run/data workflows."""

import json
from pathlib import Path

import yaml
from typer.testing import CliRunner

from tradingchassis_ops_lab.cli import app
from tradingchassis_ops_lab.data.prepare import prepare_dataset
from tradingchassis_ops_lab.engines.nautilus.backtest import NautilusSmokeBacktestResult

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


def _write_valid_spec(
    path: Path,
    run_id: str = "run-spec-cli-run",
    mode: str = "backtest",
) -> None:
    spec = {
        "spec_version": "v1",
        "run_id": run_id,
        "mode": mode,
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
    assert "run-spec-cli-run" in result.stdout


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
    _write_valid_spec(spec_path, run_id="run-spec-cli-run-init")

    result = runner.invoke(app, ["run", "init", "--spec", str(spec_path)])
    assert result.exit_code == 0
    assert "Initialized run artifacts at" in result.stdout
    assert "config_sha256=" in result.stdout

    run_dir = tmp_path / "artifacts" / "runs" / "run-spec-cli-run-init"
    assert run_dir.is_dir()
    assert (run_dir / "run_spec.yaml").is_file()
    assert (run_dir / "metadata.json").is_file()
    assert (run_dir / "journal.jsonl").is_file()


def test_tc_run_init_fails_for_duplicate_run_id(tmp_path: Path, monkeypatch) -> None:
    """Init command fails cleanly when run artifacts already exist."""
    monkeypatch.chdir(tmp_path)
    spec_path = tmp_path / "valid.yaml"
    _write_valid_spec(spec_path, run_id="run-spec-duplicate-run")

    first = runner.invoke(app, ["run", "init", "--spec", str(spec_path)])
    second = runner.invoke(app, ["run", "init", "--spec", str(spec_path)])
    assert first.exit_code == 0
    assert second.exit_code != 0
    assert "Run artifacts already exist" in second.stderr


def test_tc_run_backtest_creates_lifecycle_artifacts(tmp_path: Path, monkeypatch) -> None:
    """Backtest command creates final minimal NautilusTrader smoke lifecycle artifact set."""
    monkeypatch.chdir(tmp_path)
    prepare_dataset(dataset="btcusdt-sample", data_root=Path("data"))
    spec_path = tmp_path / "backtest.yaml"
    _write_valid_spec(spec_path, run_id="smoke-backtest-backtest-run")

    result = runner.invoke(app, ["run", "backtest", "--spec", str(spec_path)])
    assert result.exit_code == 0
    assert "Backtest lifecycle artifacts at" in result.stdout
    assert "config_sha256=" in result.stdout
    assert "status=completed" in result.stdout

    run_dir = tmp_path / "artifacts" / "runs" / "smoke-backtest-backtest-run"
    assert run_dir.is_dir()
    assert (run_dir / "run_spec.yaml").is_file()
    assert (run_dir / "metadata.json").is_file()
    assert (run_dir / "journal.jsonl").is_file()
    assert (run_dir / "metrics.json").is_file()
    assert (run_dir / "report.md").is_file()

    metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["status"] == "completed"
    assert metadata["started_at_utc"]
    assert metadata["completed_at_utc"]
    assert metadata["lifecycle"] == "backtest_nautilus_smoke"
    assert metadata["is_placeholder"] is False
    assert metadata["engine_execution"]["status"] == "completed"
    assert metadata["engine_execution"]["engine"] == "nautilus"
    assert metadata["engine_execution"]["nautilus_version"] == "1.227.0"
    assert metadata["engine_execution"]["error"] is None

    journal_lines = (run_dir / "journal.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(journal_lines) == 4
    journal = [json.loads(line) for line in journal_lines]
    assert [entry["event"] for entry in journal] == [
        "run_started",
        "backtest_started",
        "backtest_completed",
        "run_completed",
    ]
    assert journal[-1]["status"] == "completed"
    assert all(entry["event"] != "run_initialized" for entry in journal)
    assert journal[2]["result"] == "engine_smoke_completed"
    assert journal[2]["input_candles_count"] == 20
    assert journal[2]["bars_processed"] == 20

    metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["engine_executed"] is True
    assert metrics["is_placeholder"] is False
    assert metrics["input_candles_count"] == 20
    assert metrics["bars_processed"] == 20
    assert isinstance(metrics["engine_duration_ms"], int)
    assert metrics["metrics"] == {}

    report = (run_dir / "report.md").read_text(encoding="utf-8")
    assert "minimal NautilusTrader engine smoke backtest" in report
    assert "not a validated strategy performance report" in report
    assert "No profitability claims are made" in report
    assert "No orders, fills, or PnL metrics are produced" in report
    assert "Sharpe" not in report


def test_tc_run_backtest_fails_when_prepared_dataset_is_missing(
    tmp_path: Path, monkeypatch
) -> None:
    """Backtest command fails clearly before data preparation."""
    monkeypatch.chdir(tmp_path)
    spec_path = tmp_path / "missing-data.yaml"
    _write_valid_spec(spec_path, run_id="smoke-backtest-missing-dataset")

    result = runner.invoke(app, ["run", "backtest", "--spec", str(spec_path)])
    assert result.exit_code != 0
    assert "Run tc data prepare --dataset btcusdt-sample first." in result.stderr


def test_tc_run_backtest_fails_for_paper_mode(tmp_path: Path, monkeypatch) -> None:
    """Backtest command rejects specs that are not mode=backtest."""
    monkeypatch.chdir(tmp_path)
    spec_path = tmp_path / "paper.yaml"
    _write_valid_spec(spec_path, run_id="smoke-backtest-paper-run", mode="paper")

    result = runner.invoke(app, ["run", "backtest", "--spec", str(spec_path)])
    assert result.exit_code != 0
    assert "Spec mode must be backtest" in result.stderr


def test_tc_run_backtest_fails_for_duplicate_run_id(tmp_path: Path, monkeypatch) -> None:
    """Backtest command fails cleanly when run artifacts already exist."""
    monkeypatch.chdir(tmp_path)
    spec_path = tmp_path / "dup.yaml"
    _write_valid_spec(spec_path, run_id="smoke-backtest-backtest-duplicate")

    def _fake_smoke(**kwargs):
        del kwargs
        return NautilusSmokeBacktestResult(
            dataset="btcusdt-sample",
            input_candles_count=20,
            bars_processed=20,
            engine_duration_ms=1,
            nautilus_version="1.227.0",
        )

    monkeypatch.setattr(
        "tradingchassis_ops_lab.runs.backtest.run_nautilus_backtest_smoke", _fake_smoke
    )

    first = runner.invoke(app, ["run", "backtest", "--spec", str(spec_path)])
    second = runner.invoke(app, ["run", "backtest", "--spec", str(spec_path)])

    assert first.exit_code == 0
    assert second.exit_code != 0
    assert "Run artifacts already exist" in second.stderr


def test_tc_run_backtest_failure_writes_failed_metadata(tmp_path: Path, monkeypatch) -> None:
    """Backtest command marks run failed and appends run_failed journal event."""
    monkeypatch.chdir(tmp_path)
    prepare_dataset(dataset="btcusdt-sample", data_root=Path("data"))
    spec_path = tmp_path / "failure.yaml"
    _write_valid_spec(spec_path, run_id="smoke-backtest-backtest-failure")

    def _raise_smoke_failure(**kwargs):
        del kwargs
        raise RuntimeError("forced smoke failure")

    monkeypatch.setattr(
        "tradingchassis_ops_lab.runs.backtest.run_nautilus_backtest_smoke", _raise_smoke_failure
    )
    result = runner.invoke(app, ["run", "backtest", "--spec", str(spec_path)])
    assert result.exit_code != 0

    run_dir = tmp_path / "artifacts" / "runs" / "smoke-backtest-backtest-failure"
    assert run_dir.is_dir()

    metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["status"] == "failed"
    assert metadata["lifecycle"] == "backtest_nautilus_smoke"
    assert metadata["engine_execution"]["status"] == "failed"
    assert "forced smoke failure" in metadata["engine_execution"]["error"]
    assert metadata["engine_execution"]["completed_at_utc"]

    journal_lines = (run_dir / "journal.jsonl").read_text(encoding="utf-8").splitlines()
    journal = [json.loads(line) for line in journal_lines]
    assert [entry["event"] for entry in journal] == [
        "run_started",
        "backtest_started",
        "run_failed",
    ]


def test_tc_run_paper_creates_lifecycle_artifacts(tmp_path: Path, monkeypatch) -> None:
    """Paper command creates deterministic paper lifecycle skeleton artifact set."""
    monkeypatch.chdir(tmp_path)
    spec_path = tmp_path / "paper.yaml"
    _write_valid_spec(spec_path, run_id="paper-skeleton-paper-run", mode="paper")

    result = runner.invoke(app, ["run", "paper", "--spec", str(spec_path)])
    assert result.exit_code == 0
    assert "Paper lifecycle artifacts at" in result.stdout
    assert "config_sha256=" in result.stdout
    assert "status=completed" in result.stdout

    run_dir = tmp_path / "artifacts" / "runs" / "paper-skeleton-paper-run"
    assert run_dir.is_dir()
    assert (run_dir / "run_spec.yaml").is_file()
    assert (run_dir / "metadata.json").is_file()
    assert (run_dir / "journal.jsonl").is_file()
    assert (run_dir / "metrics.json").is_file()
    assert (run_dir / "report.md").is_file()

    metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["status"] == "completed"
    assert metadata["started_at_utc"]
    assert metadata["completed_at_utc"]
    assert metadata["lifecycle"] == "paper_skeleton"
    assert metadata["is_placeholder"] is True
    assert metadata["paper_execution"]["status"] == "completed"
    assert metadata["paper_execution"]["engine"] == "nautilus"
    assert metadata["paper_execution"]["connectivity"] == "none"
    assert metadata["paper_execution"]["session_type"] == "synthetic_heartbeat"
    assert metadata["paper_execution"]["error"] is None

    journal_lines = (run_dir / "journal.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(journal_lines) == 7
    journal = [json.loads(line) for line in journal_lines]
    assert [entry["event"] for entry in journal] == [
        "run_started",
        "paper_started",
        "paper_heartbeat",
        "paper_heartbeat",
        "paper_heartbeat",
        "paper_completed",
        "run_completed",
    ]
    assert all(entry["event"] != "run_initialized" for entry in journal)
    assert (
        journal[1]["note"] == "paper skeleton lifecycle started; no exchange/testnet connectivity"
    )
    for index, heartbeat in enumerate(journal[2:5], start=1):
        assert heartbeat["heartbeat_index"] == index
        assert heartbeat["heartbeat_total"] == 3
        assert heartbeat["synthetic"] is True
    assert journal[5]["result"] == "paper_skeleton_completed"
    assert journal[5]["heartbeat_count"] == 3
    assert journal[6]["status"] == "completed"

    metrics = json.loads((run_dir / "metrics.json").read_text(encoding="utf-8"))
    assert metrics["status"] == "completed"
    assert metrics["is_placeholder"] is True
    assert metrics["engine_executed"] is False
    assert metrics["connectivity"] == "none"
    assert metrics["paper_lifecycle"] == "synthetic_heartbeat"
    assert metrics["heartbeat_count"] == 3
    assert metrics["synthetic_duration_seconds"] == 3
    assert metrics["metrics"] == {}

    report = (run_dir / "report.md").read_text(encoding="utf-8")
    assert "Paper Skeleton Report" in report
    assert "no exchange/testnet connection" in report
    assert "no API keys or secrets" in report
    assert "no live market data" in report
    assert "no orders" in report
    assert "no fills" in report
    assert "no strategy execution" in report
    assert "not paper trading connectivity" in report


def test_tc_run_paper_fails_for_backtest_mode(tmp_path: Path, monkeypatch) -> None:
    """Paper command rejects specs that are not mode=paper."""
    monkeypatch.chdir(tmp_path)
    spec_path = tmp_path / "backtest.yaml"
    _write_valid_spec(spec_path, run_id="paper-skeleton-backtest-spec", mode="backtest")

    result = runner.invoke(app, ["run", "paper", "--spec", str(spec_path)])
    assert result.exit_code != 0
    assert "Spec mode must be paper" in result.stderr


def test_tc_run_paper_fails_for_duplicate_run_id(tmp_path: Path, monkeypatch) -> None:
    """Paper command fails cleanly when run artifacts already exist."""
    monkeypatch.chdir(tmp_path)
    spec_path = tmp_path / "dup-paper.yaml"
    _write_valid_spec(spec_path, run_id="paper-skeleton-paper-duplicate", mode="paper")

    first = runner.invoke(app, ["run", "paper", "--spec", str(spec_path)])
    second = runner.invoke(app, ["run", "paper", "--spec", str(spec_path)])

    assert first.exit_code == 0
    assert second.exit_code != 0
    assert "Run artifacts already exist" in second.stderr


def test_tc_run_paper_failure_writes_failed_metadata(tmp_path: Path, monkeypatch) -> None:
    """Paper command marks run failed and appends run_failed journal event."""
    monkeypatch.chdir(tmp_path)
    spec_path = tmp_path / "paper-failure.yaml"
    _write_valid_spec(spec_path, run_id="paper-skeleton-paper-failure", mode="paper")

    def _raise_heartbeat_failure(**kwargs):
        del kwargs
        raise RuntimeError("forced paper heartbeat failure")

    monkeypatch.setattr(
        "tradingchassis_ops_lab.runs.paper._append_synthetic_heartbeat_events",
        _raise_heartbeat_failure,
    )
    result = runner.invoke(app, ["run", "paper", "--spec", str(spec_path)])
    assert result.exit_code != 0

    run_dir = tmp_path / "artifacts" / "runs" / "paper-skeleton-paper-failure"
    assert run_dir.is_dir()

    metadata = json.loads((run_dir / "metadata.json").read_text(encoding="utf-8"))
    assert metadata["status"] == "failed"
    assert metadata["lifecycle"] == "paper_skeleton"
    assert metadata["paper_execution"]["status"] == "failed"
    assert "forced paper heartbeat failure" in metadata["paper_execution"]["error"]
    assert metadata["paper_execution"]["completed_at_utc"]
    assert "completed_at_utc" in metadata

    journal_lines = (run_dir / "journal.jsonl").read_text(encoding="utf-8").splitlines()
    journal = [json.loads(line) for line in journal_lines]
    assert [entry["event"] for entry in journal] == [
        "run_started",
        "paper_started",
        "run_failed",
    ]
    assert journal[-1]["status"] == "failed"
    assert "forced paper heartbeat failure" in journal[-1]["error"]


def test_tc_data_prepare_succeeds_and_is_idempotent(tmp_path: Path, monkeypatch) -> None:
    """Data prepare command succeeds repeatedly for the supported dataset."""
    data_root = tmp_path / "runtime-data"
    monkeypatch.setenv("TRADINGCHASSIS_OPS_LAB_DATA_ROOT", str(data_root))

    first = runner.invoke(app, ["data", "prepare", "--dataset", "btcusdt-sample"])
    second = runner.invoke(app, ["data", "prepare", "--dataset", "btcusdt-sample"])

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert "Prepared dataset=btcusdt-sample" in first.stdout
    assert (data_root / "datasets" / "btcusdt-sample" / "candles_1m.csv").is_file()


def test_tc_data_prepare_fails_for_unknown_dataset(tmp_path: Path, monkeypatch) -> None:
    """Data prepare command fails for unsupported datasets."""
    monkeypatch.setenv("TRADINGCHASSIS_OPS_LAB_DATA_ROOT", str(tmp_path / "runtime-data"))
    result = runner.invoke(app, ["data", "prepare", "--dataset", "ethusdt-sample"])
    assert result.exit_code != 0
    assert "Unsupported dataset" in result.stderr


def test_tc_data_fingerprint_fails_before_prepare(tmp_path: Path, monkeypatch) -> None:
    """Fingerprint command fails with actionable guidance when data is missing."""
    monkeypatch.setenv("TRADINGCHASSIS_OPS_LAB_DATA_ROOT", str(tmp_path / "runtime-data"))
    result = runner.invoke(app, ["data", "fingerprint", "--dataset", "btcusdt-sample"])
    assert result.exit_code != 0
    assert "tc data prepare --dataset btcusdt-sample" in result.stderr


def test_tc_data_fingerprint_succeeds_after_prepare(tmp_path: Path, monkeypatch) -> None:
    """Fingerprint command succeeds after preparing local dataset files."""
    data_root = tmp_path / "runtime-data"
    monkeypatch.setenv("TRADINGCHASSIS_OPS_LAB_DATA_ROOT", str(data_root))

    prepared = runner.invoke(app, ["data", "prepare", "--dataset", "btcusdt-sample"])
    result = runner.invoke(app, ["data", "fingerprint", "--dataset", "btcusdt-sample"])

    assert prepared.exit_code == 0
    assert result.exit_code == 0
    assert "dataset_sha256=" in result.stdout
    assert (data_root / "fingerprints" / "btcusdt-sample.fingerprint.json").is_file()


def test_tc_metrics_export_outputs_prometheus_text(tmp_path: Path, monkeypatch) -> None:
    """Metrics export command prints Prometheus exposition to stdout."""
    monkeypatch.chdir(tmp_path)
    run_id = "metrics-cli-export"
    run_dir = tmp_path / "artifacts" / "runs" / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "metadata.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "mode": "backtest",
                "engine": "nautilus",
                "venue": "binance",
                "instrument": "BTCUSDT",
                "status": "completed",
                "created_at_utc": "2026-05-20T19:00:00Z",
                "data": {"dataset": "btcusdt-sample"},
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "metrics.json").write_text(
        json.dumps(
            {
                "dataset": "btcusdt-sample",
                "is_placeholder": False,
                "engine_executed": True,
                "input_candles_count": 20,
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "journal.jsonl").write_text('{"event":"run_started"}\n', encoding="utf-8")

    result = runner.invoke(
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
    assert result.exit_code == 0
    assert "tradingchassis_ops_lab_run_info{" in result.stdout
    assert "tradingchassis_ops_lab_backtest_input_candles_total" in result.stdout


def test_tc_metrics_export_writes_output_file(tmp_path: Path, monkeypatch) -> None:
    """Metrics export command writes exposition text to output file."""
    monkeypatch.chdir(tmp_path)
    run_id = "metrics-cli-output"
    run_dir = tmp_path / "artifacts" / "runs" / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "metadata.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "mode": "paper",
                "engine": "nautilus",
                "venue": "binance_testnet",
                "instrument": "BTCUSDT",
                "status": "completed",
                "created_at_utc": "2026-05-20T19:00:00Z",
                "data": {"dataset": "btcusdt-sample"},
            }
        ),
        encoding="utf-8",
    )
    (run_dir / "metrics.json").write_text(
        json.dumps(
            {
                "is_placeholder": True,
                "engine_executed": False,
                "heartbeat_count": 3,
                "synthetic_duration_seconds": 3,
            }
        ),
        encoding="utf-8",
    )

    output_path = tmp_path / "exports" / "run.prom"
    result = runner.invoke(
        app,
        [
            "metrics",
            "export",
            "--run-id",
            run_id,
            "--artifacts-root",
            str(tmp_path / "artifacts" / "runs"),
            "--output",
            str(output_path),
            "--no-include-journal",
        ],
    )
    assert result.exit_code == 0
    assert output_path.is_file()
    assert "Exported metrics to" in result.stdout
    contents = output_path.read_text(encoding="utf-8")
    assert "tradingchassis_ops_lab_paper_heartbeat_total" in contents
    assert "tradingchassis_ops_lab_journal_events_total" not in contents


def test_tc_metrics_export_fails_for_invalid_run_id(tmp_path: Path, monkeypatch) -> None:
    """Metrics export fails with non-zero exit for missing run artifacts."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(
        app,
        [
            "metrics",
            "export",
            "--run-id",
            "missing-run",
            "--artifacts-root",
            str(tmp_path / "artifacts" / "runs"),
        ],
    )
    assert result.exit_code != 0
    assert "Run artifacts directory not found" in result.stderr


def test_tc_metrics_serve_help_exits_successfully() -> None:
    """Metrics serve help output is available."""
    result = runner.invoke(app, ["metrics", "serve", "--help"])
    assert result.exit_code == 0
    assert "artifact-derived metrics" in result.stdout


def test_tc_kill_activate_writes_runtime_files(tmp_path: Path, monkeypatch) -> None:
    """Kill activate command writes state and events files."""
    runtime_root = tmp_path / "runtime" / "kill_switch"
    monkeypatch.setenv("TRADINGCHASSIS_OPS_LAB_RUNTIME_ROOT", str(runtime_root))
    monkeypatch.setenv("USER", "test-operator")
    run_id = "kill-switch-cli-activate"

    result = runner.invoke(
        app,
        ["kill", "activate", "--run-id", run_id, "--reason", "manual stop"],
    )
    assert result.exit_code == 0
    assert f"run_id={run_id}" in result.stdout
    assert "state=active" in result.stdout
    assert "event=kill_activated" in result.stdout
    assert "reason=manual stop" in result.stdout
    assert "actor=test-operator" in result.stdout
    assert (runtime_root / f"{run_id}.state.json").is_file()
    assert (runtime_root / f"{run_id}.events.jsonl").is_file()


def test_tc_kill_status_absent_exits_zero(tmp_path: Path, monkeypatch) -> None:
    """Kill status reports absent when state file does not exist."""
    runtime_root = tmp_path / "runtime" / "kill_switch"
    monkeypatch.setenv("TRADINGCHASSIS_OPS_LAB_RUNTIME_ROOT", str(runtime_root))
    run_id = "kill-switch-cli-status-absent"

    result = runner.invoke(app, ["kill", "status", "--run-id", run_id])
    assert result.exit_code == 0
    assert f"run_id={run_id}" in result.stdout
    assert "state=absent" in result.stdout


def test_tc_kill_status_json_outputs_payload(tmp_path: Path, monkeypatch) -> None:
    """Kill status --json outputs valid JSON payload."""
    runtime_root = tmp_path / "runtime" / "kill_switch"
    monkeypatch.setenv("TRADINGCHASSIS_OPS_LAB_RUNTIME_ROOT", str(runtime_root))
    run_id = "kill-switch-cli-status-json"
    runner.invoke(
        app,
        ["kill", "activate", "--run-id", run_id, "--reason", "manual stop"],
    )

    result = runner.invoke(app, ["kill", "status", "--run-id", run_id, "--json"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "v1"
    assert payload["run_id"] == run_id
    assert payload["state"] == "active"


def test_tc_kill_clear_writes_cleared_state(tmp_path: Path, monkeypatch) -> None:
    """Kill clear command appends clear event and writes cleared state."""
    runtime_root = tmp_path / "runtime" / "kill_switch"
    monkeypatch.setenv("TRADINGCHASSIS_OPS_LAB_RUNTIME_ROOT", str(runtime_root))
    run_id = "kill-switch-cli-clear"
    runner.invoke(app, ["kill", "activate", "--run-id", run_id, "--reason", "manual stop"])

    result = runner.invoke(
        app,
        ["kill", "clear", "--run-id", run_id, "--reason", "manual reset"],
    )
    assert result.exit_code == 0
    assert f"run_id={run_id}" in result.stdout
    assert "state=cleared" in result.stdout
    assert "event=kill_cleared" in result.stdout
    assert "reason=manual reset" in result.stdout

    state_payload = json.loads((runtime_root / f"{run_id}.state.json").read_text(encoding="utf-8"))
    assert state_payload["state"] == "cleared"


def test_tc_kill_activate_fails_for_empty_reason(tmp_path: Path, monkeypatch) -> None:
    """Kill activate command fails cleanly for whitespace-only reason."""
    runtime_root = tmp_path / "runtime" / "kill_switch"
    monkeypatch.setenv("TRADINGCHASSIS_OPS_LAB_RUNTIME_ROOT", str(runtime_root))

    result = runner.invoke(
        app,
        ["kill", "activate", "--run-id", "kill-switch-cli-empty-reason", "--reason", "   "],
    )
    assert result.exit_code != 0
    assert "reason must be non-empty" in result.stderr


def test_tc_kill_status_fails_for_malformed_state_file(tmp_path: Path, monkeypatch) -> None:
    """Kill status returns non-zero for malformed state file JSON."""
    runtime_root = tmp_path / "runtime" / "kill_switch"
    monkeypatch.setenv("TRADINGCHASSIS_OPS_LAB_RUNTIME_ROOT", str(runtime_root))
    run_id = "kill-switch-cli-malformed"
    runtime_root.mkdir(parents=True)
    (runtime_root / f"{run_id}.state.json").write_text("{bad json", encoding="utf-8")

    result = runner.invoke(app, ["kill", "status", "--run-id", run_id])
    assert result.exit_code != 0
    assert "Malformed JSON in kill switch state file" in result.stderr


def _write_reconciliation_state(path: Path, *, run_id: str, freshness_max_age_seconds: int) -> None:
    payload = {
        "schema_version": "v1",
        "run_id": run_id,
        "as_of_utc": "2026-05-21T00:00:00Z",
        "position": {
            "symbol": "BTCUSDT",
            "side": "flat",
            "qty": "0",
            "avg_entry_price": None,
        },
        "open_orders": [],
        "freshness": {
            "position_ts_utc": "2026-05-21T00:00:00Z",
            "orders_ts_utc": "2026-05-21T00:00:00Z",
            "max_age_seconds": freshness_max_age_seconds,
        },
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_tc_reconcile_check_ok_writes_result_file(tmp_path: Path, monkeypatch) -> None:
    """Reconcile check exits zero for matching expected/observed fixtures."""
    monkeypatch.chdir(tmp_path)
    run_id = "reconcile-cli-ok"
    run_dir = tmp_path / "artifacts" / "runs" / run_id
    run_dir.mkdir(parents=True)

    expected_path = tmp_path / "expected.json"
    observed_path = tmp_path / "observed.json"
    _write_reconciliation_state(
        expected_path,
        run_id=run_id,
        freshness_max_age_seconds=999999999,
    )
    _write_reconciliation_state(
        observed_path,
        run_id=run_id,
        freshness_max_age_seconds=999999999,
    )

    result = runner.invoke(
        app,
        [
            "reconcile",
            "check",
            "--run-id",
            run_id,
            "--expected",
            str(expected_path),
            "--observed",
            str(observed_path),
        ],
    )
    assert result.exit_code == 0
    assert f"run_id={run_id}" in result.stdout
    assert "status=ok" in result.stdout
    assert "summary_ok=3" in result.stdout
    assert (run_dir / "reconciliation_result.json").is_file()


def test_tc_reconcile_check_mismatch_exits_non_zero(tmp_path: Path, monkeypatch) -> None:
    """Reconcile check exits non-zero for mismatching open orders."""
    monkeypatch.chdir(tmp_path)
    run_id = "reconcile-cli-mismatch"
    run_dir = tmp_path / "artifacts" / "runs" / run_id
    run_dir.mkdir(parents=True)

    expected_path = tmp_path / "expected.json"
    observed_path = tmp_path / "observed.json"
    _write_reconciliation_state(
        expected_path,
        run_id=run_id,
        freshness_max_age_seconds=999999999,
    )
    _write_reconciliation_state(
        observed_path,
        run_id=run_id,
        freshness_max_age_seconds=999999999,
    )
    expected_payload = json.loads(expected_path.read_text(encoding="utf-8"))
    expected_payload["open_orders"] = [
        {
            "order_id": "a-1",
            "symbol": "BTCUSDT",
            "side": "buy",
            "type": "limit",
            "qty": "0.2",
            "price": "101.0",
        }
    ]
    expected_path.write_text(
        json.dumps(expected_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "reconcile",
            "check",
            "--run-id",
            run_id,
            "--expected",
            str(expected_path),
            "--observed",
            str(observed_path),
        ],
    )
    assert result.exit_code != 0
    assert "status=mismatch" in result.stdout
    assert "summary_mismatch=1" in result.stdout
    assert (run_dir / "reconciliation_result.json").is_file()


def test_tc_reconcile_check_warning_exits_zero(tmp_path: Path, monkeypatch) -> None:
    """Reconcile check exits zero for warning-only freshness staleness."""
    monkeypatch.chdir(tmp_path)
    run_id = "reconcile-cli-warning"
    (tmp_path / "artifacts" / "runs" / run_id).mkdir(parents=True)

    expected_path = tmp_path / "expected.json"
    observed_path = tmp_path / "observed.json"
    _write_reconciliation_state(expected_path, run_id=run_id, freshness_max_age_seconds=999999999)
    _write_reconciliation_state(observed_path, run_id=run_id, freshness_max_age_seconds=1)
    observed_payload = json.loads(observed_path.read_text(encoding="utf-8"))
    observed_payload["freshness"]["position_ts_utc"] = "2000-01-01T00:00:00Z"
    observed_payload["freshness"]["orders_ts_utc"] = "2000-01-01T00:00:00Z"
    observed_path.write_text(
        json.dumps(observed_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "reconcile",
            "check",
            "--run-id",
            run_id,
            "--expected",
            str(expected_path),
            "--observed",
            str(observed_path),
        ],
    )
    assert result.exit_code == 0
    assert "status=warning" in result.stdout
    assert "summary_warning=1" in result.stdout


def test_tc_reconcile_check_unknown_exits_non_zero(tmp_path: Path, monkeypatch) -> None:
    """Reconcile check exits non-zero when freshness data is insufficient."""
    monkeypatch.chdir(tmp_path)
    run_id = "reconcile-cli-unknown"
    (tmp_path / "artifacts" / "runs" / run_id).mkdir(parents=True)

    expected_path = tmp_path / "expected.json"
    observed_path = tmp_path / "observed.json"
    _write_reconciliation_state(expected_path, run_id=run_id, freshness_max_age_seconds=999999999)
    _write_reconciliation_state(observed_path, run_id=run_id, freshness_max_age_seconds=999999999)
    expected_payload = json.loads(expected_path.read_text(encoding="utf-8"))
    observed_payload = json.loads(observed_path.read_text(encoding="utf-8"))
    expected_payload.pop("freshness")
    observed_payload.pop("freshness")
    expected_path.write_text(
        json.dumps(expected_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    observed_path.write_text(
        json.dumps(observed_payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    result = runner.invoke(
        app,
        [
            "reconcile",
            "check",
            "--run-id",
            run_id,
            "--expected",
            str(expected_path),
            "--observed",
            str(observed_path),
        ],
    )
    assert result.exit_code != 0
    assert "status=unknown" in result.stdout
    assert "summary_unknown=1" in result.stdout


def test_tc_reconcile_check_run_id_mismatch_fails(tmp_path: Path, monkeypatch) -> None:
    """Reconcile check fails clearly when payload run_id mismatches CLI run_id."""
    monkeypatch.chdir(tmp_path)
    run_id = "reconcile-cli-run-id"
    (tmp_path / "artifacts" / "runs" / run_id).mkdir(parents=True)

    expected_path = tmp_path / "expected.json"
    observed_path = tmp_path / "observed.json"
    _write_reconciliation_state(expected_path, run_id=run_id, freshness_max_age_seconds=999999999)
    _write_reconciliation_state(
        observed_path,
        run_id="different-run-id",
        freshness_max_age_seconds=999999999,
    )

    result = runner.invoke(
        app,
        [
            "reconcile",
            "check",
            "--run-id",
            run_id,
            "--expected",
            str(expected_path),
            "--observed",
            str(observed_path),
        ],
    )
    assert result.exit_code != 0
    assert "run_id mismatch" in result.stderr


def test_tc_reconcile_check_missing_run_directory_fails(tmp_path: Path, monkeypatch) -> None:
    """Reconcile check fails when run artifact directory does not exist."""
    monkeypatch.chdir(tmp_path)
    run_id = "reconcile-cli-missing-run-dir"
    expected_path = tmp_path / "expected.json"
    observed_path = tmp_path / "observed.json"
    _write_reconciliation_state(expected_path, run_id=run_id, freshness_max_age_seconds=999999999)
    _write_reconciliation_state(observed_path, run_id=run_id, freshness_max_age_seconds=999999999)

    result = runner.invoke(
        app,
        [
            "reconcile",
            "check",
            "--run-id",
            run_id,
            "--expected",
            str(expected_path),
            "--observed",
            str(observed_path),
        ],
    )
    assert result.exit_code != 0
    assert "Run artifacts directory not found" in result.stderr


def test_tc_reconcile_check_appends_journal_when_present(tmp_path: Path, monkeypatch) -> None:
    """Reconcile check appends compact reconciliation event when journal exists."""
    monkeypatch.chdir(tmp_path)
    run_id = "reconcile-cli-journal"
    run_dir = tmp_path / "artifacts" / "runs" / run_id
    run_dir.mkdir(parents=True)
    journal_path = run_dir / "journal.jsonl"
    journal_path.write_text('{"event":"run_started"}\n', encoding="utf-8")

    expected_path = tmp_path / "expected.json"
    observed_path = tmp_path / "observed.json"
    _write_reconciliation_state(
        expected_path,
        run_id=run_id,
        freshness_max_age_seconds=999999999,
    )
    _write_reconciliation_state(
        observed_path,
        run_id=run_id,
        freshness_max_age_seconds=999999999,
    )

    result = runner.invoke(
        app,
        [
            "reconcile",
            "check",
            "--run-id",
            run_id,
            "--expected",
            str(expected_path),
            "--observed",
            str(observed_path),
        ],
    )
    assert result.exit_code == 0
    lines = journal_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    payload = json.loads(lines[-1])
    assert payload["event"] == "reconciliation_checked"


def _write_minimal_run_artifacts_for_drill(tmp_path: Path, run_id: str, with_journal: bool) -> Path:
    run_dir = tmp_path / "artifacts" / "runs" / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "run_spec.yaml").write_text("spec_version: v1\n", encoding="utf-8")
    (run_dir / "metadata.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "mode": "paper",
                "engine": "nautilus",
                "venue": "binance_testnet",
                "instrument": "BTCUSDT",
                "status": "completed",
                "created_at_utc": "2026-05-20T19:00:00Z",
                "data": {"dataset": "btcusdt-sample"},
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (run_dir / "metrics.json").write_text(
        json.dumps(
            {"is_placeholder": True, "engine_executed": False},
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    if with_journal:
        (run_dir / "journal.jsonl").write_text('{"event":"run_started"}\n', encoding="utf-8")
    return run_dir


def test_tc_drill_stale_market_data_succeeds(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_id = "drill-cli-stale"
    _write_minimal_run_artifacts_for_drill(tmp_path, run_id=run_id, with_journal=True)

    result = runner.invoke(app, ["drill", "stale-market-data", "--run-id", run_id])
    assert result.exit_code == 0
    assert f"run_id={run_id}" in result.stdout
    assert "drill_name=stale_market_data" in result.stdout
    assert "outcome=expected_warning" in result.stdout
    assert "status=completed" in result.stdout

    report_path = tmp_path / "artifacts" / "runs" / run_id / "drills" / "stale_market_data.json"
    assert report_path.is_file()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["outcome"] == "expected_warning"


def test_tc_drill_reconciliation_mismatch_exits_non_zero_by_design(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.chdir(tmp_path)
    run_id = "drill-cli-mismatch"
    _write_minimal_run_artifacts_for_drill(tmp_path, run_id=run_id, with_journal=True)

    result = runner.invoke(app, ["drill", "reconciliation-mismatch", "--run-id", run_id])
    assert result.exit_code != 0
    assert f"run_id={run_id}" in result.stdout
    assert "drill_name=reconciliation_mismatch" in result.stdout
    assert "outcome=expected_mismatch" in result.stdout
    assert "status=completed" in result.stdout
    assert "Expected non-zero exit" in result.stderr

    report_path = (
        tmp_path / "artifacts" / "runs" / run_id / "drills" / "reconciliation_mismatch.json"
    )
    assert report_path.is_file()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["outcome"] == "expected_mismatch"


def test_tc_drill_restart_recovery_succeeds(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_id = "drill-cli-restart"
    _write_minimal_run_artifacts_for_drill(tmp_path, run_id=run_id, with_journal=False)

    result = runner.invoke(app, ["drill", "restart-recovery", "--run-id", run_id])
    assert result.exit_code == 0
    assert f"run_id={run_id}" in result.stdout
    assert "drill_name=restart_recovery" in result.stdout
    assert "outcome=simulated_recovery_ok" in result.stdout
    assert "status=completed" in result.stdout

    report_path = tmp_path / "artifacts" / "runs" / run_id / "drills" / "restart_recovery.json"
    assert report_path.is_file()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert (
        report["statement"]
        == "no process restart performed; this is artifact-based recovery rehearsal"
    )


def test_tc_drill_missing_run_directory_fails(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_id = "drill-cli-missing"
    result = runner.invoke(app, ["drill", "stale-market-data", "--run-id", run_id])
    assert result.exit_code != 0
    assert "Run artifacts directory not found" in result.stderr
