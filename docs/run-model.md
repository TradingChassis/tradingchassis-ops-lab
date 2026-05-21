# Run Model

## What is a run?

A run is a single, identifiable execution of a trading workflow in either `backtest` or `paper` mode.
Each run is defined by a spec and produces traceable metadata, journal entries, and artifacts.
Example specs are in `examples/configs/`.

## Core concepts

- **run_id**: unique identifier for a run instance
- **run spec**: declaration of mode, instrument, strategy reference, and run configuration
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

- `artifacts/runs/<run_id>/reconciliation_result.json`
- `artifacts/runs/<run_id>/drills/*.json`
- `artifacts/runs/<run_id>/metrics.prom` (when exported to file)

## Why reproducibility and traceability matter

- Reproducibility allows the same run inputs to be rerun with consistent expectations.
- Traceability allows operators to answer what ran, when, with which inputs, and why a result occurred.
- Together they support practical debugging, review, and drill validation.

## Concrete examples

- Backtest example: `examples/configs/btcusdt_backtest.yaml`
- Paper example: `examples/configs/btcusdt_paper.yaml`

For the end-to-end runnable sequence, see `Quickstart` and `Full demo flow` in `README.md`.
