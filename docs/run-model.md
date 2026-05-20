# Run Model

## What is a run?

A run is a single, identifiable execution of a trading workflow in either `backtest` or `paper` mode.
Each run is defined by a versioned spec and produces traceable metadata, journal entries, and artifacts.

## Core concepts

- **run_id**: unique identifier for a run instance
- **run spec**: versioned declaration of mode, instrument, strategy reference, and run configuration
- **immutable inputs**: exact config/data/code references used for that run
- **metadata**: operational facts (timestamps, status, mode, identifiers)
- **hashes**: fingerprints for config/data/code inputs to support reproducibility checks
- **artifacts**: run outputs in a stable layout
- **journal**: operational event log for the run lifecycle
- **report**: concise summary of outcome, checks, and notable events

## Why reproducibility and traceability matter

- Reproducibility allows the same run inputs to be rerun with consistent expectations.
- Traceability allows operators to answer what ran, when, with which inputs, and why a result occurred.
- Together they support practical debugging, review, and drill validation.

## Illustrative example (schema placeholder)

This YAML is illustrative only. The final schema will be implemented in a later slice.

```yaml
run_id: "run-2026-05-20T190000Z-backtest-btcusdt"
mode: "backtest"
instrument: "BTCUSDT"
strategy: "toy_strategy_v1"
spec_version: "v1"
inputs:
  config_ref: "configs/backtest/toy-btcusdt.yaml"
  data_ref: "data/btcusdt/sample-dataset.parquet"
  code_ref: "git:abc1234"
hashes:
  config_sha256: "<placeholder>"
  data_sha256: "<placeholder>"
  code_sha256: "<placeholder>"
artifacts_root: "artifacts/run-2026-05-20T190000Z-backtest-btcusdt/"
```
