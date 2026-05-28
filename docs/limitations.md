# Limitations

This project is intentionally constrained in its current implementation.

- Local-only operations lab; no live exchange connectivity
- NautilusTrader-only engine scope
- Single example instrument scope (`BTCUSDT`)
- Example data support is **1-minute OHLCV candles** only (`candles_1m.csv`); **orderbook / LOB data is not supported** (deferred to future work)
- Backtest path is a **Nautilus engine smoke run** over prepared candles, not a strategy performance report or custom strategy harness
- RunSpec `strategy` fields (for example `ops_smoke_demo`) provide scenario identity and currently select only built-in local scenarios; no custom strategy loading or plugin-style strategy extension yet
- RunSpec `data.fingerprint` is metadata/reserved and is not a runtime enforcement gate yet
- RunSpec `observability.journal|metrics|report` fields are metadata/reserved; current lifecycle paths still write standard artifacts
- RunSpec `connectivity_readiness` is local readiness contract metadata (env var names only), not real provider credential validation
- In current examples, RunSpec venue values `binance` and `binance_testnet` are label-only; they do not indicate active exchange/testnet/live connectivity
- `tc connectivity readiness` is local preflight only: env placeholder presence check, no network calls, no exchange/testnet/live connectivity
- `tc connectivity probe` is local loopback-only preflight: read-only HTTP `GET` against loopback URL only, no exchange/testnet/live connectivity
- Probe results are artifact-backed (`connectivity_probe.json`) and probe metrics are derived from artifacts, not live external telemetry
- Probe does not store response body, response headers, or secret values
- Readiness does not fetch balances, positions, account state, or external runtime state
- Readiness does not submit/cancel orders and does not flatten positions
- Probe does not submit/cancel orders and does not flatten positions
- Readiness metrics are artifact-backed and do not expose env var names or env var values
- No secret storage in readiness artifacts, metadata, journal, report, or metrics
- Paper path is a **bounded synthetic lifecycle skeleton** with no market data feed and no exchange/testnet connectivity
- Kill switch behavior is file-based and local
- Reconciliation is file-based, fixture-driven, and report-only
- Failure drills are deterministic artifact checks, not real orchestration
- No profitability/alpha claim
- No production-grade safety, reliability, or low-latency claim

These limitations are deliberate to keep the current implementation focused on operational workflow quality rather than breadth or performance claims.
