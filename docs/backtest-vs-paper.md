# Backtest vs Paper

Both modes are first-class run modes in the current implementation and share the same operational framing: specs, run metadata, hashes, artifacts, journal, and reports.
For runnable commands, see [Quickstart](quickstart.md) and [Demo Flow](demo-flow.md).

Neither mode is real paper trading, live trading, or exchange/testnet connectivity. Paper is a **bounded synthetic lifecycle skeleton** used to exercise local ops workflows.

## Comparison

| Aspect | Backtest | Paper |
|---|---|---|
| time model | Simulated/historical replay window | Bounded local session with synthetic heartbeats (wall-clock pacing only) |
| data source | Prepared local **1m OHLCV candles** from fixtures | No market data feed; no live or historical feed |
| duration | Finite smoke replay | Short fixed synthetic session |
| failure modes | Dataset/preparation issues, engine smoke failures | Local lifecycle/safety gate issues (not feed outages) |
| reconciliation | File-based expected vs observed checks | Same file-based checks (fixture-driven) |
| observability | Run progress plus artifact-backed scenario counters and Prometheus export | Synthetic heartbeat and safety metrics |
| output artifacts | Smoke run outputs and summary reports | Skeleton session outputs and summary reports |
| connectivity | Local fixture-driven Nautilus smoke path | No exchange, testnet, or live connectivity |
| strategy execution | One built-in local scenario strategy (`ops_smoke_demo`) over bars; deterministic action only | None (lifecycle skeleton only) |
| `strategy` config semantics | Scenario identity metadata; selects only built-in scenarios (no dynamic custom loading) | Same metadata semantics, no execution |
| order activity / performance | No order submission (`orders_submitted = 0`, `fills_count = 0`) and no PnL/performance reporting | No orders and no PnL/performance reporting |

## What is shared

- Common run identity and metadata model
- Common spec-driven workflow and hash tracking
- Common artifact layout principles
- Common operational journal expectations
- Common safety and reconciliation intent
