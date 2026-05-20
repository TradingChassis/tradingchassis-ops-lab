"""CLI tests for core commands and run/data workflows."""

import json
from pathlib import Path

import yaml
from typer.testing import CliRunner

from ops_lab.cli import app
from ops_lab.data.prepare import prepare_dataset
from ops_lab.engines.nautilus.backtest import NautilusSmokeBacktestResult

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
    run_id: str = "slice2-cli-run",
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


def test_tc_run_backtest_creates_lifecycle_artifacts(tmp_path: Path, monkeypatch) -> None:
    """Backtest command creates final Slice 5 smoke lifecycle artifact set."""
    monkeypatch.chdir(tmp_path)
    prepare_dataset(dataset="btcusdt-sample", data_root=Path("data"))
    spec_path = tmp_path / "backtest.yaml"
    _write_valid_spec(spec_path, run_id="slice5-backtest-run")

    result = runner.invoke(app, ["run", "backtest", "--spec", str(spec_path)])
    assert result.exit_code == 0
    assert "Backtest lifecycle artifacts at" in result.stdout
    assert "config_sha256=" in result.stdout
    assert "status=completed" in result.stdout

    run_dir = tmp_path / "artifacts" / "runs" / "slice5-backtest-run"
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
    _write_valid_spec(spec_path, run_id="slice5-missing-dataset")

    result = runner.invoke(app, ["run", "backtest", "--spec", str(spec_path)])
    assert result.exit_code != 0
    assert "Run tc data prepare --dataset btcusdt-sample first." in result.stderr


def test_tc_run_backtest_fails_for_paper_mode(tmp_path: Path, monkeypatch) -> None:
    """Backtest command rejects specs that are not mode=backtest."""
    monkeypatch.chdir(tmp_path)
    spec_path = tmp_path / "paper.yaml"
    _write_valid_spec(spec_path, run_id="slice5-paper-run", mode="paper")

    result = runner.invoke(app, ["run", "backtest", "--spec", str(spec_path)])
    assert result.exit_code != 0
    assert "Spec mode must be backtest" in result.stderr


def test_tc_run_backtest_fails_for_duplicate_run_id(tmp_path: Path, monkeypatch) -> None:
    """Backtest command fails cleanly when run artifacts already exist."""
    monkeypatch.chdir(tmp_path)
    spec_path = tmp_path / "dup.yaml"
    _write_valid_spec(spec_path, run_id="slice5-backtest-duplicate")

    def _fake_smoke(**kwargs):
        del kwargs
        return NautilusSmokeBacktestResult(
            dataset="btcusdt-sample",
            input_candles_count=20,
            bars_processed=20,
            engine_duration_ms=1,
            nautilus_version="1.227.0",
        )

    monkeypatch.setattr("ops_lab.runs.backtest.run_nautilus_backtest_smoke", _fake_smoke)

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
    _write_valid_spec(spec_path, run_id="slice5-backtest-failure")

    def _raise_smoke_failure(**kwargs):
        del kwargs
        raise RuntimeError("forced smoke failure")

    monkeypatch.setattr("ops_lab.runs.backtest.run_nautilus_backtest_smoke", _raise_smoke_failure)
    result = runner.invoke(app, ["run", "backtest", "--spec", str(spec_path)])
    assert result.exit_code != 0

    run_dir = tmp_path / "artifacts" / "runs" / "slice5-backtest-failure"
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


def test_tc_data_prepare_succeeds_and_is_idempotent(tmp_path: Path, monkeypatch) -> None:
    """Data prepare command succeeds repeatedly for the supported dataset."""
    data_root = tmp_path / "runtime-data"
    monkeypatch.setenv("OPS_LAB_DATA_ROOT", str(data_root))

    first = runner.invoke(app, ["data", "prepare", "--dataset", "btcusdt-sample"])
    second = runner.invoke(app, ["data", "prepare", "--dataset", "btcusdt-sample"])

    assert first.exit_code == 0
    assert second.exit_code == 0
    assert "Prepared dataset=btcusdt-sample" in first.stdout
    assert (data_root / "datasets" / "btcusdt-sample" / "candles_1m.csv").is_file()


def test_tc_data_prepare_fails_for_unknown_dataset(tmp_path: Path, monkeypatch) -> None:
    """Data prepare command fails for unsupported datasets."""
    monkeypatch.setenv("OPS_LAB_DATA_ROOT", str(tmp_path / "runtime-data"))
    result = runner.invoke(app, ["data", "prepare", "--dataset", "ethusdt-sample"])
    assert result.exit_code != 0
    assert "Unsupported dataset" in result.stderr


def test_tc_data_fingerprint_fails_before_prepare(tmp_path: Path, monkeypatch) -> None:
    """Fingerprint command fails with actionable guidance when data is missing."""
    monkeypatch.setenv("OPS_LAB_DATA_ROOT", str(tmp_path / "runtime-data"))
    result = runner.invoke(app, ["data", "fingerprint", "--dataset", "btcusdt-sample"])
    assert result.exit_code != 0
    assert "tc data prepare --dataset btcusdt-sample" in result.stderr


def test_tc_data_fingerprint_succeeds_after_prepare(tmp_path: Path, monkeypatch) -> None:
    """Fingerprint command succeeds after preparing local dataset files."""
    data_root = tmp_path / "runtime-data"
    monkeypatch.setenv("OPS_LAB_DATA_ROOT", str(data_root))

    prepared = runner.invoke(app, ["data", "prepare", "--dataset", "btcusdt-sample"])
    result = runner.invoke(app, ["data", "fingerprint", "--dataset", "btcusdt-sample"])

    assert prepared.exit_code == 0
    assert result.exit_code == 0
    assert "dataset_sha256=" in result.stdout
    assert (data_root / "fingerprints" / "btcusdt-sample.fingerprint.json").is_file()
