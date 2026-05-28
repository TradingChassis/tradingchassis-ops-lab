# Run Model

## What is a run?

A run is a single, identifiable execution of a trading workflow in either `backtest` or `paper` mode.
Each run is defined by a spec and produces traceable metadata, journal entries, and artifacts.
Example specs are in `examples/configs/`.

## Core concepts

- **run_id**: unique identifier for a run instance
- **run spec**: declaration of mode, instrument, scenario identity metadata (`strategy`), and run configuration
- **immutable inputs**: exact config/data/code references used for that run
- **metadata**: operational facts (timestamps, status, mode, identifiers)
- **hashes**: fingerprints for config/data/code inputs to support reproducibility checks
- **artifacts**: run outputs in a stable layout
- **journal**: operational event log for the run lifecycle
- **report**: concise summary of outcome, checks, and notable events

## Artifact contract (current implementation)

For a given `run_id`, the local artifact contract is:

- `artifacts/runs/<run_id>/run_spec.yaml`
- `artifacts/runs/<run_id>/metadata.json`
- `artifacts/runs/<run_id>/journal.jsonl`
- `artifacts/runs/<run_id>/metrics.json`
- `artifacts/runs/<run_id>/report.md`

Optional/additional outputs depending on commands:

- `artifacts/runs/<run_id>/connectivity_readiness.json`
- `artifacts/runs/<run_id>/reconciliation_result.json`
- `artifacts/runs/<run_id>/drills/*.json`
- `artifacts/runs/<run_id>/metrics.prom` (when exported to file)

## Why reproducibility and traceability matter

- Reproducibility allows the same run inputs to be rerun with consistent expectations.
- Traceability allows operators to answer what ran, when, with which inputs, and why a result occurred.
- Together they support practical debugging, review, and drill validation.

## Current strategy/scenario contract

- The current backtest path is a Nautilus engine smoke run over prepared 1-minute OHLCV candles.
- `strategy.name` and `strategy.version` are used as scenario identity/traceability metadata.
- Backtest currently supports one built-in scenario mapping: `ops_smoke_demo`.
- The backtest path registers the built-in Nautilus strategy for `ops_smoke_demo`.
- Scenario execution records deterministic operational counters (`strategy_registered`, `bars_seen`, `deterministic_action_triggered`, `orders_submitted`, `fills_count`) in `metadata.json`, `metrics.json`, `journal.jsonl`, and `report.md`.
- Scenario metrics export is artifact-backed via `tc metrics export --run-id <run_id>`.
- `ops_smoke_demo` does not submit orders (`orders_submitted = 0`, `fills_count = 0`).
- No PnL/Sharpe/returns/profitability/alpha performance reporting is included in the current scenario contract.
- Current runs do not dynamically load custom strategy modules from config.
- `strategy.name` values such as `ops_smoke_demo` identify local smoke/demo intent, not alpha claims.

## Current reserved config fields

- `data.fingerprint` is stored for metadata/traceability and is not a runtime gate yet.
- `observability.journal`, `observability.metrics`, and `observability.report` are stored in metadata;
  current lifecycle paths still write standard artifacts regardless of toggle values.
- `connectivity_readiness` is a reserved local-only contract for readiness metadata (env var names only).
- The `connectivity_readiness` block participates in config hashing.
- RunSpec parsing does not perform env lookup and does not perform network calls.
- Local env presence evaluation runs via `tc connectivity readiness --spec <path>` (artifact-backed preflight only).
- The readiness path writes `connectivity_readiness.json`, patches `metadata["connectivity_readiness"]`,
  appends `connectivity_readiness_evaluated` to `journal.jsonl`, and updates report readiness section only if `report.md` already exists.
- No env var values are stored in readiness artifacts, metadata, journal, or reports.
- Readiness state set is finite and local-only: `disabled`, `missing_credentials`, `configured`, `invalid_config`, `unknown`.
- Readiness metrics are artifact-backed from `connectivity_readiness.json`:
  - `tradingchassis_ops_lab_connectivity_readiness_state`
  - `tradingchassis_ops_lab_connectivity_readiness_enabled`
  - `tradingchassis_ops_lab_connectivity_readiness_missing_required_env_total`
  - `tradingchassis_ops_lab_connectivity_readiness_probe_performed`

## Concrete examples

- Backtest example: `examples/configs/btcusdt_backtest.yaml`
- Paper example: `examples/configs/btcusdt_paper.yaml`

For the end-to-end runnable sequence, see [Quickstart](quickstart.md) and [Demo Flow](demo-flow.md).
