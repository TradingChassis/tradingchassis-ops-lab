# Backtest vs Paper

Both modes are first-class run modes in the current implementation and share the same operational framing: specs, run metadata, hashes, artifacts, journal, and reports.
For runnable commands, see [Quickstart](quickstart.md) and [Demo Flow](demo-flow.md).

Neither mode is real paper trading, live trading, or exchange/testnet connectivity. Paper is a **bounded synthetic lifecycle skeleton** used to exercise local ops workflows.

## Operational evidence workflow

Backtest and paper are intentionally different operational modes. The comparison workflow captures artifact-backed operational evidence, not trading equivalence:

```bash
tc evidence compare --backtest-run-id <backtest_run_id> --paper-run-id <paper_run_id>
```

Outputs:

- `artifacts/evidence/<backtest_run_id>__<paper_run_id>/backtest_vs_paper_evidence.json`
- `artifacts/evidence/<backtest_run_id>__<paper_run_id>/backtest_vs_paper_evidence.md`

What this evidence helps you learn:

- which operational facts are shared across both runs
- which differences are expected by mode design
- which required artifacts are present/missing
- which journal events are shared or mode-specific
- which known gaps are explicit in current scope

It does not evaluate strategy performance and does not compare PnL, Sharpe, returns, or profitability.

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

## Expected mode differences

For current local workflows, `comparison_status = differences_expected` is often the normal outcome:

- backtest executes a candle-driven engine smoke path
- paper is a synthetic lifecycle skeleton
- venue labels and config fingerprints can differ across mode-specific specs
- paper may contain safety/readiness/probe state snapshots
- backtest may contain scenario/bar execution facts

These are expected mode differences, not evidence of strategy quality.

## Known gaps (current scope)

- no PnL or strategy performance analytics
- no slippage or fill-quality analysis
- no external venue state reconciliation
- candle-only operational backtest path
- one built-in local scenario (`ops_smoke_demo`)
- no live/testnet trading behavior
