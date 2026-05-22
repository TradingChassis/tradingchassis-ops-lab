# Demo Flow

Canonical run IDs used below:

- Backtest: `2026-05-20-btcusdt-backtest-001`
- Paper: `2026-05-20-btcusdt-paper-001`

How to choose `<run_id>`:

- Read `run_id` from the spec file under `examples/configs/`, or
- Inspect `artifacts/runs/<run_id>/` and use an existing run directory name.

## 1) Setup

```bash
python -m pip install -e ".[dev]"
scripts/check.sh
```

## 2) Prepare and fingerprint local synthetic data

```bash
tc data prepare --dataset btcusdt-sample
tc data fingerprint --dataset btcusdt-sample
```

Expected artifact locations:

- `data/datasets/`
- `data/fingerprints/`

## 3) Run backtest smoke run

```bash
tc run backtest --spec examples/configs/btcusdt_backtest.yaml
```

Expected artifact location:

- `artifacts/runs/2026-05-20-btcusdt-backtest-001/`

## 4) Run paper lifecycle skeleton

```bash
tc run paper --spec examples/configs/btcusdt_paper.yaml
```

Expected artifact location:

- `artifacts/runs/2026-05-20-btcusdt-paper-001/`

## 5) Export metrics

```bash
tc metrics export --run-id 2026-05-20-btcusdt-backtest-001
tc metrics export --run-id 2026-05-20-btcusdt-paper-001 --output artifacts/runs/2026-05-20-btcusdt-paper-001/metrics.prom
```

Expected artifact location:

- `artifacts/runs/<run_id>/`

## 6) Local observability stack demo

Artifact-backed run outputs under `artifacts/runs/<run_id>/` are rendered as Prometheus text by `tc metrics serve`. Prometheus scrapes that local endpoint, and Grafana visualizes run and operational state from those scraped metrics.

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
- Target `tradingchassis_ops_lab_metrics` should be `UP`
- Grafana: `http://localhost:${TC_GRAFANA_PORT:-3000}`
- Open `TradingChassis Ops Lab Run Observability`
- Confirm panel `Kill Switch State` shows the selected run's local safety snapshot state

This demo flow is local-only and artifact-backed. It is not live production monitoring, and it does not imply exchange/testnet connectivity or strategy-performance tracking.

## 7) Runtime safety demo flow (paper)

```bash
tc kill activate --run-id 2026-05-20-btcusdt-paper-001 --reason "demo block"
tc run paper --spec examples/configs/btcusdt_paper.yaml
```

Expected blocked run behavior:

- CLI reports `status=safety_blocked`
- full run artifacts are still written under `artifacts/runs/2026-05-20-btcusdt-paper-001/`
- journal includes `paper_safety_checked` and `paper_safety_blocked`
- report includes `## Safety status`
- `tc metrics export --run-id 2026-05-20-btcusdt-paper-001` includes `tradingchassis_ops_lab_kill_switch_state`

Clear and rerun:

```bash
tc kill clear --run-id 2026-05-20-btcusdt-paper-001 --reason "demo clear"
tc run paper --spec examples/configs/btcusdt_paper.yaml
```

Expected cleared/normal behavior:

- use a fresh run ID (recommended) or clean old artifacts first
- paper lifecycle follows normal synthetic heartbeat behavior
- status is `completed`
- safety state is reflected as `cleared` or `absent` in metadata and exported metrics

This runtime safety demo is a local file-based gate. It does not perform order cancellation, position flattening, exchange/testnet/live connectivity, or provide production safety guarantees.

Expected artifact location for kill-switch state files:

- `runtime/kill_switch/`

## 8) Reconciliation check

```bash
tc reconcile check --run-id 2026-05-20-btcusdt-paper-001 --expected examples/reconciliation/expected_match.json --observed examples/reconciliation/observed_match.json
```

Expected artifact location:

- `artifacts/runs/2026-05-20-btcusdt-paper-001/`

## 9) Failure drills

```bash
tc drill stale-market-data --run-id 2026-05-20-btcusdt-paper-001
tc drill reconciliation-mismatch --run-id 2026-05-20-btcusdt-paper-001
tc drill restart-recovery --run-id 2026-05-20-btcusdt-paper-001
```

`tc drill reconciliation-mismatch --run-id 2026-05-20-btcusdt-paper-001` is expected to exit non-zero by design when mismatch is detected.

Expected artifact locations:

- `artifacts/runs/2026-05-20-btcusdt-paper-001/`
- `reports/sample/`
