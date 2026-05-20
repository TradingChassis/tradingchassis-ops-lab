# Scope

## In scope (v1)

- Operations-focused run lab around NautilusTrader
- One engine: NautilusTrader
- One example instrument: BTCUSDT
- One intentionally simple toy strategy
- Two run modes: backtest and paper
- Local-first execution model
- Reproducible runs from versioned run specs
- Run metadata with config/data/code hashes
- Predictable artifact layout, operational journal, and basic reports
- Basic observability hooks
- Reconciliation checks and kill switch behavior
- Three failure drills:
  - stale market data
  - forced reconciliation mismatch
  - restart/recovery

Implemented in current repository scope:
- Local data prepare/fingerprint workflow
- Spec-driven backtest smoke run and paper lifecycle skeleton
- Artifact-driven metrics export
- File-based kill switch workflow
- File-based reconciliation checks
- Deterministic failure drills with runbooks

## Out of scope (v1)

- Building a custom trading engine
- Building a strategy library or quant research platform
- Live trading with production-grade reliability requirements
- Low-latency gateway engineering
- Profitability or alpha claims
- Multi-engine or broad multi-instrument framework design
- Generic Kubernetes platform work
- Full production observability stack hardening

Future work beyond v1 may expand depth, but this repository intentionally keeps the current implementation local, reproducible, and non-production.

## Definition of Done (v1)

v1 is complete when a user can run one NautilusTrader backtest smoke workflow and one paper lifecycle skeleton workflow from versioned specs, inspect artifacts/reports, export metrics, exercise file-based safety/reconciliation behavior, and run/read three deterministic failure drills and runbooks.
