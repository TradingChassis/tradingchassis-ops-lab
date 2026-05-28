# Quickstart

Install, run checks, prepare sample data, run one smoke backtest, and bring up the local observability stack.

```bash
python -m pip install -e ".[dev]"
scripts/check.sh
tc data prepare --dataset btcusdt-sample
tc data fingerprint --dataset btcusdt-sample
tc run backtest --spec examples/configs/btcusdt_backtest.yaml
```

The backtest command runs a **Nautilus engine smoke path** over prepared **1-minute OHLCV candles** with one built-in local scenario (`ops_smoke_demo`). It registers a strategy, increments `bars_seen`, triggers one deterministic scenario action, and writes operational counters to run artifacts (`metadata.json`, `metrics.json`, `journal.jsonl`, `report.md`). It is not a custom strategy harness and does not dynamically load user strategy modules.

Current demo boundaries for this command:

- `orders_submitted = 0`
- `fills_count = 0`
- no PnL/Sharpe/returns/profitability/alpha reporting

## Local paths

| Path | Role |
| --- | --- |
| `src/tradingchassis_ops_lab/data/` | Tracked source helpers for dataset prepare/fingerprint |
| `data/` | Ignored local prepared input (`datasets/`, `fingerprints/`) |
| `artifacts/runs/` | Ignored generated per-run outputs |
| `reports/sample/` | Tracked curated examples for review |

Expected artifact locations after the commands above:

- `data/datasets/`
- `data/fingerprints/`
- `artifacts/runs/2026-05-20-btcusdt-backtest-001/`

## Local observability quick path

Terminal 1:

```bash
tc metrics serve --artifacts-root artifacts/runs --host 0.0.0.0 --port 8000
```

Terminal 2:

```bash
docker compose -f deploy/observability/docker-compose.yml up
```

Optional override example:

```bash
TC_METRICS_TARGET=<target>:8000 TC_PROMETHEUS_PORT=9091 TC_GRAFANA_PORT=3001 docker compose -f deploy/observability/docker-compose.yml up
```

Verification:

- Prometheus targets page: `http://localhost:${TC_PROMETHEUS_PORT:-9090}/targets`
- The `tradingchassis_ops_lab_metrics` target should be `UP`
- Grafana: `http://localhost:${TC_GRAFANA_PORT:-3000}`
- Open dashboard: `TradingChassis Ops Lab Run Observability`

Defaults:

- Prometheus port: `9090`
- Grafana port: `3000`
- Default scrape target: `host.docker.internal:8000`

Overrides:

- `TC_PROMETHEUS_PORT`
- `TC_GRAFANA_PORT`
- `TC_METRICS_TARGET`

For the complete operational walkthrough (paper skeleton, kill switch, reconciliation, drills), continue to [Demo Flow](demo-flow.md).

## Connectivity readiness quick path (local-only)

Readiness evaluation uses initialized run artifacts, so run `tc run init` first:

```bash
tc spec validate --spec examples/configs/btcusdt_paper.yaml
tc run init --spec examples/configs/btcusdt_paper.yaml
tc connectivity readiness --spec examples/configs/btcusdt_paper.yaml
```

Expected behavior:

- If required placeholder env vars are absent/empty, readiness state is `missing_credentials`.
- With non-empty dummy values, readiness state becomes `configured`:

```bash
TRADINGCHASSIS_PAPER_API_KEY=dummy TRADINGCHASSIS_PAPER_API_SECRET=dummy tc connectivity readiness --spec examples/configs/btcusdt_paper.yaml
```

- Env var values are never stored in artifacts, journal, report, or metrics output.
- No network calls are performed by the readiness command.
