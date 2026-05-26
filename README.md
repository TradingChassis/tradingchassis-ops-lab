# TradingChassis Ops Lab

**TradingChassis Ops Lab** is a local-first **trading infrastructure / operations** lab around [NautilusTrader](https://github.com/nautechsystems/nautilus_trader). It is a **Trading Infrastructure Proof of Skill**: reproducible, spec-driven run workflows, artifact-first observability, and file-based operational controls—not a strategy alpha, PnL, live trading, or production platform project.

The current backtest path is a **Nautilus engine smoke run** over prepared **1-minute OHLCV candle** data for lifecycle and artifact validation. It registers one built-in local scenario strategy (`strategy.name: ops_smoke_demo`) for deterministic operational counters. It is not a strategy performance harness and does not dynamically load user-provided strategy code. The paper path is a **bounded synthetic lifecycle skeleton** with no market data feed and no exchange or testnet connectivity.

## What you can demo now

| Release | You can demonstrate |
| --- | --- |
| **0.1.0** | Local data prepare/fingerprint; Nautilus smoke backtest; bounded paper skeleton; run artifacts/reports; reconciliation checks; failure drills and runbooks |
| **0.2.0** | Artifact-backed `tc metrics serve`; local Prometheus + Grafana stack; dashboard visibility for run metrics |
| **0.3.0** | File-based kill switch safety snapshot; paper lifecycle `safety_blocked` when kill switch is active; safety status in metadata, journal, report, metrics, and Grafana |

Full command sequence: [`docs/demo-flow.md`](docs/demo-flow.md).

## Quickstart summary

```bash
python -m pip install -e ".[dev]"
scripts/check.sh
tc data prepare --dataset btcusdt-sample
tc data fingerprint --dataset btcusdt-sample
tc run backtest --spec examples/configs/btcusdt_backtest.yaml
tc metrics export --run-id 2026-05-20-btcusdt-backtest-001
```

## Local paths

| Path | Role |
| --- | --- |
| `src/tradingchassis_ops_lab/data/` | Tracked source helpers for dataset prepare/fingerprint |
| `data/` | Ignored local prepared input (`datasets/`, `fingerprints/`) |
| `artifacts/runs/` | Ignored generated per-run outputs |
| `reports/sample/` | Tracked curated examples for review (not full runtime trees) |

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

## Runtime safety integration

- Local runtime safety state is artifact-backed and file-based.
- `tc run paper` deterministically blocks lifecycle start when kill switch state is active.
- Grafana includes `Kill Switch State` from `tradingchassis_ops_lab_kill_switch_state`.
- No real order cancellation or position flattening is included.

## Documentation

- Documentation is published with GitHub Pages from the MkDocs site (on `main`).
- Local docs home: [`docs/index.md`](docs/index.md)
- Local quickstart page: [`docs/quickstart.md`](docs/quickstart.md)
- Local full walkthrough: [`docs/demo-flow.md`](docs/demo-flow.md)
- Local roadmap: [`docs/roadmap.md`](docs/roadmap.md)
- Release changelog: [`CHANGELOG.md`](CHANGELOG.md)

## Scope guardrails

- Local-only operations lab; no live exchange connectivity
- Smoke backtest and synthetic paper lifecycle skeleton only; no custom strategy plugin surface yet
- RunSpec `data.fingerprint` and `observability.*` are currently metadata/reserved fields and are not runtime enforcement toggles
- Example data: 1-minute OHLCV candles only; orderbook/LOB data not supported (deferred)
- No profitability, alpha, production-safety, or low-latency claims
