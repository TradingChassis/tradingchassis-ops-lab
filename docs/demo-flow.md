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

## 3) Run backtest scenario demo (`ops_smoke_demo`)

```bash
tc run backtest --spec examples/configs/btcusdt_backtest.yaml
```

This backtest remains an engine smoke run over prepared 1-minute candles and currently maps
to one built-in local scenario (`ops_smoke_demo`). The spec's `strategy.name` / `strategy.version`
are scenario identity and traceability metadata, not dynamic custom strategy loading.

Scenario behavior shown in this run:

- Nautilus strategy registration for `ops_smoke_demo`
- deterministic `bars_seen` counting
- one deterministic action trigger at a fixed bar index
- operational counters persisted in artifacts
- `orders_submitted = 0` and `fills_count = 0`
- no PnL/Sharpe/returns/profitability/alpha performance claims

Expected artifact location:

- `artifacts/runs/2026-05-20-btcusdt-backtest-001/`

## 4) Inspect backtest scenario artifacts

Inspect the run directory:

- `artifacts/runs/2026-05-20-btcusdt-backtest-001/metadata.json`
- `artifacts/runs/2026-05-20-btcusdt-backtest-001/metrics.json`
- `artifacts/runs/2026-05-20-btcusdt-backtest-001/journal.jsonl`
- `artifacts/runs/2026-05-20-btcusdt-backtest-001/report.md`

Confirm the scenario execution facts are present and consistent (`strategy_registered`,
`bars_seen`, deterministic action, `orders_submitted`, `fills_count`).

## 5) Export and verify backtest scenario Prometheus metrics

```bash
tc metrics export --run-id 2026-05-20-btcusdt-backtest-001
```

Verify scenario metrics are emitted from artifact-backed counters:

- `tradingchassis_ops_lab_backtest_scenario_strategy_registered`
- `tradingchassis_ops_lab_backtest_scenario_bars_seen_total`
- `tradingchassis_ops_lab_backtest_scenario_orders_submitted_total`
- `tradingchassis_ops_lab_backtest_scenario_fills_total`
- `tradingchassis_ops_lab_backtest_scenario_deterministic_action_triggered`

This is an operational scenario demo, not a strategy-performance demo.

## 6) Run paper lifecycle skeleton

```bash
tc run paper --spec examples/configs/btcusdt_paper.yaml
```

Expected artifact location:

- `artifacts/runs/2026-05-20-btcusdt-paper-001/`

## 7) Export paper metrics (optional file output)

```bash
tc metrics export --run-id 2026-05-20-btcusdt-backtest-001
tc metrics export --run-id 2026-05-20-btcusdt-paper-001 --output artifacts/runs/2026-05-20-btcusdt-paper-001/metrics.prom
```

Expected artifact location:

- `artifacts/runs/<run_id>/`

## 8) Connectivity readiness demo (local preflight only)

Use a spec that includes `connectivity_readiness` (for example `examples/configs/btcusdt_paper.yaml`).

Initialize run artifacts first (required):

```bash
tc run init --spec examples/configs/btcusdt_paper.yaml
```

Run readiness without env vars:

```bash
tc connectivity readiness --spec examples/configs/btcusdt_paper.yaml
```

Inspect readiness outputs:

- `artifacts/runs/2026-05-20-btcusdt-paper-001/connectivity_readiness.json`
- `artifacts/runs/2026-05-20-btcusdt-paper-001/metadata.json`
- `artifacts/runs/2026-05-20-btcusdt-paper-001/journal.jsonl`
- `artifacts/runs/2026-05-20-btcusdt-paper-001/report.md` (updated only when report exists)

Expected local-only behavior:

- readiness state vocabulary is finite: `disabled`, `missing_credentials`, `configured`, `invalid_config`, `unknown`
- state is typically `missing_credentials` without required env vars
- `probe_performed=false`
- no network calls

Run readiness with dummy non-empty env vars:

```bash
TRADINGCHASSIS_PAPER_API_KEY=dummy TRADINGCHASSIS_PAPER_API_SECRET=dummy tc connectivity readiness --spec examples/configs/btcusdt_paper.yaml
```

Expected result:

- state changes to `configured`
- dummy env values are not written into artifacts, journal, report, or command output

Readiness metrics caveat:

- `tc metrics export` reads run artifacts and requires the usual `metrics.json` artifact.
- A readiness-only sequence (`tc run init` + `tc connectivity readiness`) does not create `metrics.json`.
- For readiness-only runs, use artifact inspection as the primary validation path.
- Export readiness metrics after a lifecycle that creates `metrics.json`; creating a minimal `metrics.json` is test/dev-only, not the default user workflow.

## 9) Connectivity probe demo (local loopback only)

Use `examples/configs/btcusdt_paper.yaml` below for a quick, runnable read-through (canonical `run_id`: `2026-05-20-btcusdt-paper-001`). If artifacts for that `run_id` already exist, or you are repeating this demo, copy the example spec to a new path and change `run_id`—do not edit tracked examples in the repository.

Initialize run artifacts first (required):

```bash
tc run init --spec examples/configs/btcusdt_paper.yaml
```

Start a local fake HTTP endpoint on loopback:

```bash
mkdir -p tmp/probe-server && printf "ok\n" > tmp/probe-server/health
python -m http.server 18082 --bind 127.0.0.1 --directory tmp/probe-server
```

Run connectivity probe:

```bash
tc connectivity probe --spec examples/configs/btcusdt_paper.yaml --url http://127.0.0.1:18082/health
```

Inspect probe outputs:

- `artifacts/runs/2026-05-20-btcusdt-paper-001/connectivity_probe.json`
- `artifacts/runs/2026-05-20-btcusdt-paper-001/metadata.json`
- `artifacts/runs/2026-05-20-btcusdt-paper-001/journal.jsonl`
- `artifacts/runs/2026-05-20-btcusdt-paper-001/report.md` (updated only when report exists)

Expected probe states:

- `probe_ok` for local 2xx response
- `probe_http_error` for local non-2xx response
- `probe_unreachable` when no local server is listening
- `probe_timeout` when probe exceeds timeout

Probe boundaries:

- loopback-only target validation (`127.0.0.1`, `localhost`, `[::1]`)
- read-only `GET`
- no response body storage
- no external exchange/testnet/live connectivity

Probe metrics caveat:

- `tc metrics export` requires `metrics.json`.
- An init+probe-only sequence does not create `metrics.json`.
- For probe-only runs, artifact inspection is the primary validation path.
- For metrics/Grafana demo, use a run that already has `metrics.json` (or a minimal test/dev fixture).

## 10) Local observability stack demo

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
- Confirm panels `Connectivity Probe State` and `Connectivity Probe Latency` show probe artifact-backed values when probe metrics are present

This demo flow is local-only and artifact-backed. It is not live production monitoring, and it does not imply exchange/testnet connectivity or strategy-performance tracking.

## 11) Runtime safety demo flow (paper)

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

## 12) Reconciliation check

```bash
tc reconcile check --run-id 2026-05-20-btcusdt-paper-001 --expected examples/reconciliation/expected_match.json --observed examples/reconciliation/observed_match.json
```

Expected artifact location:

- `artifacts/runs/2026-05-20-btcusdt-paper-001/`

## 13) Failure drills

```bash
tc drill stale-market-data --run-id 2026-05-20-btcusdt-paper-001
tc drill reconciliation-mismatch --run-id 2026-05-20-btcusdt-paper-001
tc drill restart-recovery --run-id 2026-05-20-btcusdt-paper-001
```

`tc drill reconciliation-mismatch --run-id 2026-05-20-btcusdt-paper-001` is expected to exit non-zero by design when mismatch is detected.

Expected artifact locations:

- `artifacts/runs/2026-05-20-btcusdt-paper-001/`
- `reports/sample/`
