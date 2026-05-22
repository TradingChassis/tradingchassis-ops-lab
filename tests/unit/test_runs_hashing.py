"""Unit tests for deterministic run config hashing."""

from pathlib import Path

import yaml

from tradingchassis_ops_lab.runs.hashing import compute_config_sha256
from tradingchassis_ops_lab.runs.spec import load_run_spec


def _spec_a() -> str:
    return """
spec_version: v1
run_id: hash-test-run
mode: backtest
engine: nautilus
venue: binance
instrument: BTCUSDT
strategy:
  name: toy_mean_reversion
  version: 0.1.0
data:
  dataset: btcusdt-sample
  fingerprint: placeholder
risk:
  profile: tiny
observability:
  journal: true
  metrics: false
  report: false
""".strip()


def _spec_same_semantics_different_order() -> str:
    return """
instrument: BTCUSDT
mode: backtest
run_id: hash-test-run
spec_version: v1
venue: binance
engine: nautilus
risk:
  profile: tiny
strategy:
  version: 0.1.0
  name: toy_mean_reversion
observability:
  report: false
  metrics: false
  journal: true
data:
  fingerprint: placeholder
  dataset: btcusdt-sample
""".strip()


def test_compute_config_sha256_is_stable_for_same_semantics(tmp_path: Path) -> None:
    first = tmp_path / "first.yaml"
    second = tmp_path / "second.yaml"
    first.write_text(_spec_a(), encoding="utf-8")
    second.write_text(_spec_same_semantics_different_order(), encoding="utf-8")

    first_hash = compute_config_sha256(load_run_spec(first))
    second_hash = compute_config_sha256(load_run_spec(second))
    assert first_hash == second_hash


def test_compute_config_sha256_changes_when_config_changes(tmp_path: Path) -> None:
    first = tmp_path / "first.yaml"
    second = tmp_path / "second.yaml"
    first.write_text(_spec_a(), encoding="utf-8")

    changed = yaml.safe_load(_spec_a())
    changed["risk"]["profile"] = "small"
    second.write_text(yaml.safe_dump(changed), encoding="utf-8")

    first_hash = compute_config_sha256(load_run_spec(first))
    second_hash = compute_config_sha256(load_run_spec(second))
    assert first_hash != second_hash
