# Scope

## In scope (current implementation)

- Operations-focused run lab around NautilusTrader
- One engine: NautilusTrader
- One example instrument: BTCUSDT
- RunSpec **strategy metadata** (name/version) as scenario identity for traceability (e.g. `ops_smoke_demo`) with one built-in local scenario path; no custom strategy execution surface yet
- Two run modes: backtest and paper
- Local-first execution model
- Reproducible runs from run specs
- Run metadata with config/data/code hashes
- Predictable artifact layout, operational journal, and basic reports
- Basic observability hooks
- Reconciliation checks and kill switch behavior
- Fixture-backed **1-minute OHLCV candle** data prepare/fingerprint workflow
- `data.fingerprint` and `observability.*` are currently metadata/reserved fields (not runtime gating toggles)
- RunSpec `connectivity_readiness` contract with env placeholder validation and local-only readiness evaluation command
- Readiness artifacts (`connectivity_readiness.json`), metadata summary patch, journal event, and optional report section update
- Artifact-backed readiness Prometheus metrics derived from `connectivity_readiness.json`
- Three failure drills:
  - stale market data
  - forced reconciliation mismatch
  - restart/recovery

Implemented in current repository scope:

- Local data prepare/fingerprint workflow
- Spec-driven Nautilus smoke backtest and bounded synthetic paper lifecycle skeleton
- Artifact-driven metrics export
- File-based kill switch workflow
- File-based reconciliation checks
- Deterministic failure drills with runbooks

## Out of scope (current implementation)

- Building a custom trading engine
- Building a strategy library, quant research platform, or custom strategy plugin loader
- Orderbook / limit-order-book (LOB) data ingestion or replay
- Live trading with production-grade reliability requirements
- Real exchange/testnet/live connectivity checks in readiness paths
- Provider-side credential validation or secret verification
- Account/balance/position fetching
- Order submission, cancel/replace, or position flattening
- External reconciliation against provider APIs
- Adapter framework and multi-venue architecture
- Low-latency gateway engineering
- Profitability or alpha claims
- Multi-engine or broad multi-instrument framework design
- Generic Kubernetes platform work
- Full production observability stack hardening

Future work may expand depth, but this repository intentionally keeps the current implementation local, reproducible, and non-production.

## Definition of Done (current scope)

The current scope is complete when a user can run one NautilusTrader backtest smoke workflow and one paper lifecycle skeleton workflow from run specs, inspect artifacts/reports, export metrics, exercise file-based safety/reconciliation behavior, and run/read three deterministic failure drills and runbooks.
