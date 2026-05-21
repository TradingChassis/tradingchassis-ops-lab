# Limitations

This project is intentionally constrained in its current implementation.

- Local-only operations lab; no live exchange connectivity
- NautilusTrader-only engine scope
- Single example instrument scope (`BTCUSDT`)
- Intentionally simple toy strategy profile
- Backtest path is a smoke backtest, not a strategy performance report
- Paper path is a lifecycle skeleton with no exchange/testnet connectivity
- Kill switch behavior is file-based and local
- Reconciliation is file-based, fixture-driven, and report-only
- Failure drills are deterministic artifact checks, not real orchestration
- No profitability/alpha claim
- No production-grade safety, reliability, or low-latency claim

These limitations are deliberate to keep the current implementation focused on operational workflow quality rather than breadth or performance claims.
