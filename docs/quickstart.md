# Quickstart

Install, run checks, prepare sample data, run one smoke backtest, and bring up the local observability stack.

```bash
python -m pip install -e ".[dev]"
scripts/check.sh
tc data prepare --dataset btcusdt-sample
tc data fingerprint --dataset btcusdt-sample
tc run backtest --spec examples/configs/btcusdt_backtest.yaml
```

Expected artifact locations:

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

For the complete operational walkthrough, continue to [Demo Flow](demo-flow.md).
