# TradingChassis Ops Lab

**TradingChassis Ops Lab** is a local-first **trading infrastructure / operations** lab around [NautilusTrader](https://github.com/nautechsystems/nautilus_trader). It is a **trading infrastructure proof-of-skill** project: reproducible, spec-driven run workflows, artifact-first observability, and file-based operational controls.

**What it is not:** an alpha research project, PnL project, production trading system, live trading system, or generic trading platform. It does not claim profitability, alpha, or production-grade safety or latency.

The current backtest path runs the **Nautilus engine** over prepared **1-minute OHLCV candle** data for lifecycle and artifact validation. It registers one built-in local scenario strategy (`strategy.name: ops_smoke_demo`) that counts bars, triggers a deterministic action, and records operational counters—it does not submit orders and does not report PnL, alpha, or performance metrics. Custom strategy loading is deferred. The paper path is a **bounded synthetic lifecycle skeleton** with no market data feed and no exchange or testnet connectivity.

## Current capabilities

Local workflows supported today:

| Workflow | What it does |
| --- | --- |
| Data prepare / fingerprint | Prepare sample datasets and record content fingerprints |
| Nautilus backtest | Run a local smoke backtest over prepared candles with built-in `ops_smoke_demo` |
| Paper lifecycle | Run a bounded synthetic paper skeleton (no market feed, no exchange connectivity) |
| Connectivity readiness | Evaluate local env placeholder presence and write deterministic readiness artifacts |
| Artifacts & reports | Generate per-run artifacts, reports, and reconciliation checks |
| Metrics | Export run metrics and serve them for scraping |
| Observability | Run local Prometheus + Grafana against artifact-backed metrics |
| Runtime safety | File-based kill switch; paper lifecycle blocks when kill switch is active |

Command walkthrough: [`docs/demo-flow.md`](docs/demo-flow.md). Run model and specs: [`docs/run-model.md`](docs/run-model.md).

Connectivity readiness is local-only preflight: `tc connectivity readiness --spec <path>` checks env var placeholder presence (names only), writes `connectivity_readiness.json`, updates metadata/journal (and report section if present), and performs no network calls. It does not validate credentials against providers and does not imply exchange/testnet/live connectivity. Readiness metrics are available through `tc metrics export` once the run has the normal exporter artifacts (including `metrics.json`).

### Milestone history

| Version | Summary |
| --- | --- |
| `0.1.0` | Local run, artifact, and ops baseline |
| `0.2.0` | Local observability stack |
| `0.3.0` | Runtime safety integration |
| `0.4.0` | Local backtest scenario / strategy contract (`ops_smoke_demo`) |
| `0.5.0` | Connectivity readiness contract, local evaluation, and artifact-backed readiness metrics |

## Quickstart summary

```bash
python -m pip install -e ".[dev]"
scripts/check.sh
tc data prepare --dataset btcusdt-sample
tc data fingerprint --dataset btcusdt-sample
tc run backtest --spec examples/configs/btcusdt_backtest.yaml
tc metrics export --run-id 2026-05-20-btcusdt-backtest-001
```

More detail: [`docs/quickstart.md`](docs/quickstart.md), [`docs/demo-flow.md`](docs/demo-flow.md), and [`docs/run-model.md`](docs/run-model.md).

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

Default verification URLs:

- Prometheus targets: `http://localhost:9090/targets`
- Grafana: `http://localhost:3000` — open dashboard **TradingChassis Ops Lab Run Observability**

If you use non-default ports, set `TC_PROMETHEUS_PORT` and/or `TC_GRAFANA_PORT` when starting Compose, then open the same paths on your chosen local ports. `TC_METRICS_TARGET` selects which host:port Prometheus scrapes (defaults to the metrics serve endpoint).

Optional local override example:

```bash
TC_METRICS_TARGET=<target>:8000 TC_PROMETHEUS_PORT=9091 TC_GRAFANA_PORT=3001 docker compose -f deploy/observability/docker-compose.yml up
```

After that override, for example: `http://localhost:9091/targets` and `http://localhost:3001`.

## Runtime safety integration

- Local runtime safety state is artifact-backed and file-based.
- `tc run paper` blocks lifecycle start when kill switch state is active (`safety_blocked`).
- Safety status appears in metadata, journal, report, metrics, and Grafana (`Kill Switch State` from `tradingchassis_ops_lab_kill_switch_state`).
- No real order cancellation or position flattening is included.

## Documentation

- Documentation is published with GitHub Pages from the MkDocs site (on `main`).
- Docs home: [`docs/index.md`](docs/index.md)
- Quickstart: [`docs/quickstart.md`](docs/quickstart.md)
- Full walkthrough: [`docs/demo-flow.md`](docs/demo-flow.md)
- Run model: [`docs/run-model.md`](docs/run-model.md)
- Roadmap: [`docs/roadmap.md`](docs/roadmap.md)
- Changelog: [`CHANGELOG.md`](CHANGELOG.md)

## Deferred and out of scope

- **Not production trading** — local lab only; no live exchange, testnet, or production deployment (Kubernetes/GitOps deferred).
- **No custom strategy plugins** — built-in `ops_smoke_demo` only; user-provided strategy loading deferred.
- **No order submission in `ops_smoke_demo`** — deterministic operational counters only.
- **No PnL / alpha / profitability claims** — not a strategy performance harness.
- **Candle data only** — example workflows use 1-minute OHLCV; orderbook/L2 deferred.
- RunSpec `data.fingerprint` and `observability.*` are metadata/reserved fields today, not runtime enforcement toggles.
