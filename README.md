# ops-lab

## What this is

`ops-lab` is a small, operations-focused run lab around NautilusTrader.
It is designed to demonstrate reproducible backtest and paper trading workflows with clear run specs, run metadata, hashes, artifacts, and operational checks.

In under 60 seconds: this repository focuses on running and inspecting trading workflows reliably, not on inventing a new trading engine or proving strategy performance.

## What this is not

- A custom trading engine
- A strategy library
- A quant research platform
- A trading bot
- A production-grade live trading system
- A low-latency execution gateway
- A profitability claim
- A generic Kubernetes showcase

## v1 scope

- One engine: NautilusTrader
- One example instrument: BTCUSDT
- One intentionally simple toy strategy
- Two run modes: backtest and paper
- Local-first execution
- Docker Compose for Prometheus/Grafana in a later slice
- Optional Kubernetes manifests only as a final extension
- Three failure drills:
  1. stale market data
  2. forced reconciliation mismatch
  3. restart/recovery

## Planned v1 artifacts

- Versioned run specs
- Run metadata (including config/data/code hashes)
- Structured artifact layout
- Operational journal
- Basic reports
- Observability hooks
- Reconciliation checks
- Kill switch behavior
- Runbooks for the three failure drills

## Current status

Slice 0 is complete when documentation is in place only.
No implementation logic is included yet, and no claims are made that execution workflows already exist.

## Slice 3 local data workflow

Prepare the local synthetic sample dataset and compute its deterministic fingerprint:

```bash
tc data prepare --dataset btcusdt-sample
tc data fingerprint --dataset btcusdt-sample
```

Use the printed `dataset_sha256` value as the `data.fingerprint` field in your run spec.

## Slice 5 minimal Nautilus smoke backtest

Run the minimal NautilusTrader smoke backtest from a validated spec:

```bash
tc run backtest --spec examples/configs/btcusdt_backtest.yaml
```

This command runs a minimal NautilusTrader engine smoke backtest and writes lifecycle artifacts.
It loads prepared fixture candles and converts them to Nautilus bars before execution.
This is not a validated strategy performance report.
No profitability claims are made, and no orders/fills/PnL metrics are produced.

## Slice 6 paper lifecycle skeleton

Run the bounded deterministic paper-mode lifecycle skeleton from a validated spec:

```bash
tc run paper --spec examples/configs/btcusdt_paper.yaml
```

This command writes paper lifecycle skeleton artifacts only.
It does not connect to any exchange or testnet and does not execute paper trading connectivity.

## Slice 7 artifact-driven metrics export

Run a backtest or paper workflow first so artifacts exist under `artifacts/runs/<run_id>/`.

Export Prometheus text metrics from existing artifacts:

```bash
tc metrics export --run-id <run_id>
tc metrics export --run-id <run_id> --output artifacts/runs/<run_id>/metrics.prom
```

Slice 7 observability is artifact-driven and local-only.
It does not start a monitoring daemon or long-running metrics exporter.

## Slice 8 file-based kill switch

Use the minimal kill switch safety signal commands:

```bash
tc kill activate --run-id <run_id> --reason "manual stop"
tc kill status --run-id <run_id>
tc kill clear --run-id <run_id> --reason "manual reset"
```

This is a file-based operational safety signal for local workflows.
It does not cancel orders, flatten positions, or connect to exchanges.
