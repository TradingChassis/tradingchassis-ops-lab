# TradingChassis Ops Lab

`TradingChassis Ops Lab` is a local-first trading operations lab around [NautilusTrader](https://github.com/nautechsystems/nautilus_trader). It focuses on reproducible, spec-driven `backtest` and `paper` workflows with deterministic local data preparation, artifact-first observability, and file-based operational controls.

The backtest path is a smoke backtest for lifecycle and artifact validation, not a strategy performance report. The paper path is a lifecycle skeleton with no exchange or testnet connectivity.

## Quickstart summary

```bash
python -m pip install -e ".[dev]"
scripts/check.sh
tc data prepare --dataset btcusdt-sample
tc data fingerprint --dataset btcusdt-sample
tc run backtest --spec examples/configs/btcusdt_backtest.yaml
tc metrics export --run-id 2026-05-20-btcusdt-backtest-001
```

## Local observability stack

Run the local metrics endpoint (inside the Dev Container or host shell):

```bash
tc metrics serve --artifacts-root artifacts/runs --host 0.0.0.0 --port 8000
```

Start local Prometheus + Grafana:

```bash
docker compose -f deploy/observability/docker-compose.yml up
```

Optional local override example:

```bash
TC_METRICS_TARGET=<target>:8000 TC_PROMETHEUS_PORT=9091 TC_GRAFANA_PORT=3001 docker compose -f deploy/observability/docker-compose.yml up
```

Verification:

- Prometheus targets: `http://localhost:${TC_PROMETHEUS_PORT:-9090}/targets`
- Grafana dashboard: `http://localhost:${TC_GRAFANA_PORT:-3000}` then open `TradingChassis Ops Lab Run Observability`

## Runtime safety integration (`0.3.0`)

- Local runtime safety state is artifact-backed and file-based.
- `tc run paper` deterministically blocks lifecycle start when kill switch state is active.
- Grafana includes `Kill Switch State` from `tradingchassis_ops_lab_kill_switch_state`.
- No real order cancellation or position flattening is included.

## Documentation

- Documentation is published with GitHub Pages from the MkDocs site.
- Local docs home: [`docs/index.md`](docs/index.md)
- Local quickstart page: [`docs/quickstart.md`](docs/quickstart.md)
- Local full walkthrough: [`docs/demo-flow.md`](docs/demo-flow.md)
- Local roadmap: [`docs/roadmap.md`](docs/roadmap.md)
- Release changelog: [`CHANGELOG.md`](CHANGELOG.md)

## Scope guardrails

- Local-only operations lab; no live exchange connectivity
- Backtest smoke run and paper lifecycle skeleton only
- No profitability, alpha, production-safety, or low-latency claims
