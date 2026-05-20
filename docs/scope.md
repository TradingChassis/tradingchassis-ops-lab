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

## Out of scope (v1)

- Building a custom trading engine
- Building a strategy library or quant research platform
- Live trading with production-grade reliability requirements
- Low-latency gateway engineering
- Profitability or alpha claims
- Multi-engine or broad multi-instrument framework design
- Generic Kubernetes platform work
- Full production observability stack hardening

## Definition of Done (v1)

v1 is complete when a user can run one NautilusTrader backtest and one paper trading workflow from versioned specs, inspect artifacts/reports, observe basic metrics, trigger safety/reconciliation behavior, and read reports/runbooks for three failure scenarios.
