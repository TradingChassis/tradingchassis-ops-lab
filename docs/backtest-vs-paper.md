# Backtest vs Paper

Both modes are first-class run modes in the current implementation and share the same operational framing: specs, run metadata, hashes, artifacts, journal, and reports.
For runnable commands, see `README.md` (`Quickstart` and `Full demo flow`).

## Comparison

| Aspect | Backtest | Paper |
|---|---|---|
| time model | Simulated/historical clock | Real-time wall clock |
| data source | Historical market data | Paper-mode market feed |
| duration | Finite replay window | Session-oriented runtime window |
| failure modes | Dataset issues, replay assumptions | Feed interruptions, runtime instability |
| reconciliation | Compare expected replay state | Compare runtime observed state |
| observability | Run progress and result signals | Runtime health and progress signals |
| output artifacts | Replay outputs and summary reports | Session outputs and summary reports |
| connectivity | Local fixture-driven smoke path | Lifecycle skeleton only, no exchange/testnet connectivity |

## What is shared

- Common run identity and metadata model
- Common spec-driven workflow and hash tracking
- Common artifact layout principles
- Common operational journal expectations
- Common safety and reconciliation intent
