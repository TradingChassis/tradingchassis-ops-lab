# Backtest vs Paper

Both modes are first-class run modes in v1 and share the same operational framing: versioned specs, run metadata, hashes, artifacts, journal, and reports.

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

## What is shared

- Common run identity and metadata model
- Common spec-driven workflow and hash tracking
- Common artifact layout principles
- Common operational journal expectations
- Common safety and reconciliation intent
