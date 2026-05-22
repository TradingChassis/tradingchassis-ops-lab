"""Unit tests for file-based reconciliation checks."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from tradingchassis_ops_lab.reconciliation.checks import (
    ReconciliationArtifactsError,
    ReconciliationValidationError,
    run_reconciliation_check,
)


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _base_state(run_id: str) -> dict:
    return {
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
            "max_age_seconds": 60,
        },
    }


def test_exact_match_returns_ok_and_writes_result(tmp_path: Path) -> None:
    run_id = "reconcile-match"
    run_dir = tmp_path / "artifacts" / "runs" / run_id
    run_dir.mkdir(parents=True)
    expected = _base_state(run_id)
    observed = _base_state(run_id)
    expected_path = tmp_path / "expected.json"
    observed_path = tmp_path / "observed.json"
    _write_json(expected_path, expected)
    _write_json(observed_path, observed)

    result = run_reconciliation_check(
        run_id=run_id,
        expected_path=expected_path,
        observed_path=observed_path,
        artifacts_root=tmp_path / "artifacts" / "runs",
        now_utc=datetime(2026, 5, 21, 0, 0, 10, tzinfo=UTC),
    )

    assert result["status"] == "ok"
    assert result["pass"] is True
    assert result["summary"] == {"ok": 3, "warning": 0, "mismatch": 0, "unknown": 0}
    assert (run_dir / "reconciliation_result.json").is_file()


def test_position_mismatch_returns_mismatch(tmp_path: Path) -> None:
    run_id = "reconcile-position-mismatch"
    (tmp_path / "artifacts" / "runs" / run_id).mkdir(parents=True)
    expected = _base_state(run_id)
    observed = _base_state(run_id)
    observed["position"] = {
        "symbol": "BTCUSDT",
        "side": "long",
        "qty": "0.1",
        "avg_entry_price": "100.0",
    }
    expected_path = tmp_path / "expected.json"
    observed_path = tmp_path / "observed.json"
    _write_json(expected_path, expected)
    _write_json(observed_path, observed)

    result = run_reconciliation_check(
        run_id=run_id,
        expected_path=expected_path,
        observed_path=observed_path,
        artifacts_root=tmp_path / "artifacts" / "runs",
        now_utc=datetime(2026, 5, 21, 0, 0, 10, tzinfo=UTC),
    )
    assert result["status"] == "mismatch"
    assert result["pass"] is False
    assert result["checks"][0]["name"] == "position"
    assert result["checks"][0]["severity"] == "mismatch"


def test_open_order_mismatch_returns_mismatch(tmp_path: Path) -> None:
    run_id = "reconcile-order-mismatch"
    (tmp_path / "artifacts" / "runs" / run_id).mkdir(parents=True)
    expected = _base_state(run_id)
    observed = _base_state(run_id)
    expected["open_orders"] = [
        {
            "order_id": "a-1",
            "symbol": "BTCUSDT",
            "side": "buy",
            "type": "limit",
            "qty": "0.2",
            "price": "101.0",
        }
    ]
    observed["open_orders"] = []
    expected_path = tmp_path / "expected.json"
    observed_path = tmp_path / "observed.json"
    _write_json(expected_path, expected)
    _write_json(observed_path, observed)

    result = run_reconciliation_check(
        run_id=run_id,
        expected_path=expected_path,
        observed_path=observed_path,
        artifacts_root=tmp_path / "artifacts" / "runs",
        now_utc=datetime(2026, 5, 21, 0, 0, 10, tzinfo=UTC),
    )
    assert result["status"] == "mismatch"
    assert result["checks"][1]["name"] == "open_orders"
    assert result["checks"][1]["severity"] == "mismatch"


def test_stale_freshness_returns_warning(tmp_path: Path) -> None:
    run_id = "reconcile-stale"
    (tmp_path / "artifacts" / "runs" / run_id).mkdir(parents=True)
    expected = _base_state(run_id)
    observed = _base_state(run_id)
    observed["freshness"]["position_ts_utc"] = "2026-05-21T00:00:00Z"
    observed["freshness"]["orders_ts_utc"] = "2026-05-21T00:00:00Z"
    observed["freshness"]["max_age_seconds"] = 5
    expected_path = tmp_path / "expected.json"
    observed_path = tmp_path / "observed.json"
    _write_json(expected_path, expected)
    _write_json(observed_path, observed)

    result = run_reconciliation_check(
        run_id=run_id,
        expected_path=expected_path,
        observed_path=observed_path,
        artifacts_root=tmp_path / "artifacts" / "runs",
        now_utc=datetime(2026, 5, 21, 0, 0, 10, tzinfo=UTC),
    )
    assert result["status"] == "warning"
    assert result["pass"] is True
    assert result["checks"][2]["severity"] == "warning"


def test_missing_freshness_threshold_returns_unknown(tmp_path: Path) -> None:
    run_id = "reconcile-missing-freshness"
    (tmp_path / "artifacts" / "runs" / run_id).mkdir(parents=True)
    expected = _base_state(run_id)
    observed = _base_state(run_id)
    expected.pop("freshness")
    observed.pop("freshness")
    expected_path = tmp_path / "expected.json"
    observed_path = tmp_path / "observed.json"
    _write_json(expected_path, expected)
    _write_json(observed_path, observed)

    result = run_reconciliation_check(
        run_id=run_id,
        expected_path=expected_path,
        observed_path=observed_path,
        artifacts_root=tmp_path / "artifacts" / "runs",
        now_utc=datetime(2026, 5, 21, 0, 0, 10, tzinfo=UTC),
    )
    assert result["status"] == "unknown"
    assert result["pass"] is False
    assert result["checks"][2]["severity"] == "unknown"


def test_malformed_decimal_in_position_returns_unknown(tmp_path: Path) -> None:
    run_id = "reconcile-bad-decimal"
    (tmp_path / "artifacts" / "runs" / run_id).mkdir(parents=True)
    expected = _base_state(run_id)
    observed = _base_state(run_id)
    observed["position"]["qty"] = "not-a-decimal"
    expected_path = tmp_path / "expected.json"
    observed_path = tmp_path / "observed.json"
    _write_json(expected_path, expected)
    _write_json(observed_path, observed)

    result = run_reconciliation_check(
        run_id=run_id,
        expected_path=expected_path,
        observed_path=observed_path,
        artifacts_root=tmp_path / "artifacts" / "runs",
        now_utc=datetime(2026, 5, 21, 0, 0, 10, tzinfo=UTC),
    )
    assert result["status"] == "unknown"
    assert result["checks"][0]["severity"] == "unknown"


def test_malformed_freshness_timestamp_returns_unknown(tmp_path: Path) -> None:
    run_id = "reconcile-bad-freshness-timestamp"
    (tmp_path / "artifacts" / "runs" / run_id).mkdir(parents=True)
    expected = _base_state(run_id)
    observed = _base_state(run_id)
    observed["freshness"]["position_ts_utc"] = "not-a-timestamp"
    expected_path = tmp_path / "expected.json"
    observed_path = tmp_path / "observed.json"
    _write_json(expected_path, expected)
    _write_json(observed_path, observed)

    result = run_reconciliation_check(
        run_id=run_id,
        expected_path=expected_path,
        observed_path=observed_path,
        artifacts_root=tmp_path / "artifacts" / "runs",
        now_utc=datetime(2026, 5, 21, 0, 0, 10, tzinfo=UTC),
    )
    assert result["status"] == "unknown"
    assert result["pass"] is False
    assert result["checks"][2]["name"] == "freshness"
    assert result["checks"][2]["severity"] == "unknown"


def test_run_id_mismatch_raises_validation_error(tmp_path: Path) -> None:
    run_id = "reconcile-run-id"
    (tmp_path / "artifacts" / "runs" / run_id).mkdir(parents=True)
    expected = _base_state(run_id)
    observed = _base_state("different-run")
    expected_path = tmp_path / "expected.json"
    observed_path = tmp_path / "observed.json"
    _write_json(expected_path, expected)
    _write_json(observed_path, observed)

    with pytest.raises(ReconciliationValidationError):
        run_reconciliation_check(
            run_id=run_id,
            expected_path=expected_path,
            observed_path=observed_path,
            artifacts_root=tmp_path / "artifacts" / "runs",
        )


def test_missing_artifacts_dir_raises_error(tmp_path: Path) -> None:
    run_id = "reconcile-missing-artifacts"
    expected = _base_state(run_id)
    observed = _base_state(run_id)
    expected_path = tmp_path / "expected.json"
    observed_path = tmp_path / "observed.json"
    _write_json(expected_path, expected)
    _write_json(observed_path, observed)

    with pytest.raises(ReconciliationArtifactsError):
        run_reconciliation_check(
            run_id=run_id,
            expected_path=expected_path,
            observed_path=observed_path,
            artifacts_root=tmp_path / "artifacts" / "runs",
        )


def test_journal_append_when_present(tmp_path: Path) -> None:
    run_id = "reconcile-journal-present"
    run_dir = tmp_path / "artifacts" / "runs" / run_id
    run_dir.mkdir(parents=True)
    journal_path = run_dir / "journal.jsonl"
    journal_path.write_text('{"event":"run_started"}\n', encoding="utf-8")
    expected = _base_state(run_id)
    observed = _base_state(run_id)
    expected_path = tmp_path / "expected.json"
    observed_path = tmp_path / "observed.json"
    _write_json(expected_path, expected)
    _write_json(observed_path, observed)

    run_reconciliation_check(
        run_id=run_id,
        expected_path=expected_path,
        observed_path=observed_path,
        artifacts_root=tmp_path / "artifacts" / "runs",
        now_utc=datetime(2026, 5, 21, 0, 0, 10, tzinfo=UTC),
    )

    lines = journal_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    event = json.loads(lines[1])
    assert event["event"] == "reconciliation_checked"
    assert event["status"] == "ok"


def test_deterministic_result_ordering(tmp_path: Path) -> None:
    run_id = "reconcile-deterministic"
    run_dir = tmp_path / "artifacts" / "runs" / run_id
    run_dir.mkdir(parents=True)
    expected = _base_state(run_id)
    observed = _base_state(run_id)
    expected_path = tmp_path / "expected.json"
    observed_path = tmp_path / "observed.json"
    _write_json(expected_path, expected)
    _write_json(observed_path, observed)

    first = run_reconciliation_check(
        run_id=run_id,
        expected_path=expected_path,
        observed_path=observed_path,
        artifacts_root=tmp_path / "artifacts" / "runs",
        now_utc=datetime(2026, 5, 21, 0, 0, 10, tzinfo=UTC),
    )
    second = run_reconciliation_check(
        run_id=run_id,
        expected_path=expected_path,
        observed_path=observed_path,
        artifacts_root=tmp_path / "artifacts" / "runs",
        now_utc=datetime(2026, 5, 21, 0, 0, 10, tzinfo=UTC),
    )

    assert [check["name"] for check in first["checks"]] == ["position", "open_orders", "freshness"]
    assert first["status"] == second["status"]
