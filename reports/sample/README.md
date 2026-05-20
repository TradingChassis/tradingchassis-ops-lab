# Curated Sample Artifacts

This directory contains small, curated examples of `ops-lab` run outputs for portfolio review.
These files are representative, not full runtime trees.

## Provenance and curation policy

- Source commands are the same commands documented in `README.md`.
- Samples are hand-curated from representative local outputs.
- Machine-specific absolute paths are redacted.
- Actor/user fields are redacted where applicable.
- Timestamps may be retained for readability.
- These samples are not claimed as byte-for-byte reproducible snapshots.

## Sample index

Backtest sample (`reports/sample/backtest/`):
- `metadata.json`: representative output from `tc run backtest --spec examples/configs/btcusdt_backtest.yaml`
- `metrics.json`: representative run metrics from the same backtest
- `report.md`: representative run summary from the same backtest
- `journal_excerpt.jsonl`: short excerpt from run journal events
- `metrics.prom`: representative output from `tc metrics export --run-id <backtest_run_id> --output ...`

Paper sample (`reports/sample/paper/`):
- `metadata.json`: representative output from `tc run paper --spec examples/configs/btcusdt_paper.yaml`
- `metrics.json`: representative run metrics from the same paper skeleton run
- `report.md`: representative run summary from the same paper skeleton run
- `journal_excerpt.jsonl`: short excerpt from run journal events

Reconciliation sample (`reports/sample/reconciliation/`):
- `ok.json`: representative `reconciliation_result.json` from `tc reconcile check` with `expected_match.json` + `observed_match.json`
- `warning_stale.json`: representative warning result from stale freshness fixture
- `mismatch_position.json`: representative mismatch result from position mismatch fixture
- `unknown_freshness.json`: representative unknown result from missing freshness fixture

Failure drill sample (`reports/sample/drills/`):
- `stale_market_data.json`: representative output from `tc drill stale-market-data --run-id <run_id>`
- `reconciliation_mismatch.json`: representative output from `tc drill reconciliation-mismatch --run-id <run_id>`
- `restart_recovery.json`: representative output from `tc drill restart-recovery --run-id <run_id>`

## Not included by design

- Full generated trees under `artifacts/runs/**`
- Runtime kill switch state under `runtime/**`
- Prepared data files under `data/**`
