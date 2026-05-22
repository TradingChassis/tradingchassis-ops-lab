"""Unit tests for run journal helpers."""

import json
from pathlib import Path

import yaml

from tradingchassis_ops_lab.runs.journal import append_journal_event, build_run_initialized_event
from tradingchassis_ops_lab.runs.spec import load_run_spec


def _write_valid_spec(path: Path, run_id: str = "run-spec-journal-run") -> None:
    path.write_text(
        yaml.safe_dump(
            {
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
        ),
        encoding="utf-8",
    )


def test_append_journal_event_writes_run_initialized_jsonl(tmp_path: Path) -> None:
    spec_path = tmp_path / "spec.yaml"
    artifacts_dir = tmp_path / "artifacts" / "runs" / "run-spec-journal-run"
    artifacts_dir.mkdir(parents=True)
    _write_valid_spec(spec_path)
    spec = load_run_spec(spec_path)

    event = build_run_initialized_event(
        spec=spec,
        spec_path=spec_path,
        artifacts_dir=artifacts_dir,
        config_sha256="feedface",
    )
    journal_path = artifacts_dir / "journal.jsonl"
    append_journal_event(journal_path, event)

    lines = journal_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1

    parsed = json.loads(lines[0])
    assert parsed["event"] == "run_initialized"
    assert parsed["run_id"] == "run-spec-journal-run"
    assert parsed["status"] == "initialized"
    assert parsed["config_sha256"] == "feedface"
