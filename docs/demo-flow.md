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

## 5) Optional: inspect backtest scenario Prometheus metrics (debug)

This step is optional. It is not required for Grafana or Prometheus — use `tc metrics serve` (section 10) for the dashboard workflow.

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

## 7) Optional: inspect paper metrics (debug)

Optional one-shot inspection only — not a prerequisite for `tc metrics serve` or Grafana.

```bash
tc metrics export --run-id 2026-05-20-btcusdt-backtest-001
tc metrics export --run-id 2026-05-20-btcusdt-paper-001 --output artifacts/runs/2026-05-20-btcusdt-paper-001/metrics.prom
```

Expected artifact location:

- `artifacts/runs/<run_id>/`

## Backtest vs Paper Evidence

After backtest and paper artifacts exist, generate one cross-run operational evidence artifact:

```bash
tc evidence compare --backtest-run-id 2026-05-20-btcusdt-backtest-001 --paper-run-id 2026-05-20-btcusdt-paper-001
```

Inspect outputs:

- `artifacts/evidence/2026-05-20-btcusdt-backtest-001__2026-05-20-btcusdt-paper-001/backtest_vs_paper_evidence.json`
- `artifacts/evidence/2026-05-20-btcusdt-backtest-001__2026-05-20-btcusdt-paper-001/backtest_vs_paper_evidence.md`

Expected operational result for this local demo path is typically:

- `comparison_status = differences_expected`

Expected differences are useful evidence, not failures:

- backtest executes engine flow over prepared candles
- paper is a synthetic lifecycle skeleton
- config hashes or venue labels can differ by design
- paper includes safety/readiness/probe state artifacts when evaluated
- backtest includes scenario/bar execution facts
- known gaps are explicit and expected in this phase

This evidence explains operational comparability boundaries; it is not a strategy performance comparison.

For Grafana visibility, ensure `tc metrics serve` includes evidence root:

```bash
tc metrics serve --artifacts-root artifacts/runs --evidence-root artifacts/evidence --host 0.0.0.0 --port 8000
```

Check dashboard panels:

- `Backtest vs Paper Evidence Status`
- `Evidence Known Gaps`

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

- The artifact-backed metrics renderer (`tc metrics serve` and `tc metrics export`) requires the usual `metrics.json` artifact.
- A readiness-only sequence (`tc run init` + `tc connectivity readiness`) does not create `metrics.json`.
- For readiness-only runs, use artifact inspection as the primary validation path.
- Readiness metrics appear in Prometheus/Grafana after a lifecycle that creates `metrics.json`; creating a minimal `metrics.json` is test/dev-only, not the default user workflow.

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

- The artifact-backed metrics renderer (`tc metrics serve` and `tc metrics export`) requires `metrics.json`.
- An init+probe-only sequence does not create `metrics.json`.
- For probe-only runs, artifact inspection is the primary validation path.
- For the Grafana demo, use a run that already has `metrics.json` (or a minimal test/dev fixture) and start `tc metrics serve` — no prior `export` is needed.

## 10) Local observability stack demo

Run artifacts → `tc metrics serve` → Prometheus → Grafana. Sections 5 and 7 (`tc metrics export`) are optional debug checks only; they do not prepare metrics for the dashboard.

Artifact-backed run outputs under `artifacts/runs/<run_id>/` are rendered as Prometheus text by `tc metrics serve`. Prometheus scrapes that local `/metrics` endpoint, and Grafana visualizes run and operational state from those scraped metrics.

Terminal 1:

```bash
tc metrics serve --artifacts-root artifacts/runs --evidence-root artifacts/evidence --host 0.0.0.0 --port 8000
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
- Confirm evidence panels `Backtest vs Paper Evidence Status` and `Evidence Known Gaps` when evidence artifacts exist under `artifacts/evidence/`
- Confirm failure drill panels `Reconciliation Status`, `Failure Drill Last Pass`, and `Failure Drill Outcome` when drill artifacts exist under `artifacts/runs/<run_id>/drills/` (see section 13)

### Reading the Grafana dashboard

The dashboard is artifact-backed. It helps inspect completed local runs and evidence artifacts. It does not stream live trading state. Values should be read as operational signals and known boundaries, not as trading performance.

Use `tc metrics serve` for Prometheus/Grafana. Use `tc metrics export` only for optional one-shot debugging or inspection; `export` is not required before `serve`.

| Panel | What it means | What it does not mean |
| --- | --- | --- |
| `Evidence Known Gaps` | Count of explicit known limitations recorded in evidence artifacts (for example no PnL, no slippage, no fill quality, no external venue state, candle-only data, synthetic paper lifecycle). | Errors, test failures, or missing CI checks. |
| `Backtest vs Paper Evidence Status` | Encoded operational evidence status. `1` means `differences_expected` in the normal demo flow: backtest and paper differ in expected, documented ways. | Strategy performance, profitability, or trading equivalence between modes. |
| `Paper Heartbeats` | Count of synthetic paper lifecycle heartbeat events from run artifacts. | Market data events, orders, fills, or real paper trading activity. |
| `Connectivity Readiness` | Local readiness state from env placeholder presence (for example `missing_credentials` or `configured`). | Network connectivity, provider credential validation, or successful exchange/testnet access. |
| `Connectivity Probe State` | Result of a local loopback read-only HTTP probe (for example `probe_ok`, `probe_http_error`, `probe_timeout`, `probe_unreachable`). | Binance, testnet, or live exchange connectivity. |
| `Connectivity Probe Latency` | Duration of the local loopback probe in seconds. | Exchange latency or live trading latency. |
| `Kill Switch State` | Local file-based kill-switch state such as `absent`, `cleared`, or `active`. | Real order cancellation, position flattening, or a production safety guarantee. |
| Backtest scenario counters (`bars seen`, `orders submitted`, `fills`, deterministic action) | Built-in `ops_smoke_demo` operational counters from artifact-backed metrics. | PnL, alpha, profitability, or custom strategy plugin results. |
| `Run Info` / `Run Duration` | Selected run metadata and artifact-backed lifecycle timing. | Live process health or real-time runtime monitoring. |
| `Reconciliation Status` | Artifact-backed reconciliation status from `reconciliation_result.json` (`warning`, `mismatch`, `ok`). Populated after running a drill or `tc reconcile check`. | Live reconciliation, external venue state, or account or balance validation. |
| `Failure Drill Last Pass` | Encoded pass/fail from `drills/*.json`. `1`=pass, `0`=fail, `-1`=unknown. Populated after running a drill. | Live trading behavior or real operational controls. |
| `Failure Drill Outcome` | Encoded outcome from `drills/*.json`. `1`=expected_warning, `2`=expected_mismatch, `3`=simulated_recovery_ok, `-1`=unknown. | Live incident state or production alerting. |

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

## 13) Failure drills and observability (0.8.0)

For a complete inventory of local failure modes — including artifact health failures, safety blocks,
probe outcomes, evidence gaps, and observability issues — see [Failure modes](failure-modes.md).

### Run the failure drills

```bash
tc drill stale-market-data --run-id 2026-05-20-btcusdt-paper-001
tc drill reconciliation-mismatch --run-id 2026-05-20-btcusdt-paper-001
tc drill restart-recovery --run-id 2026-05-20-btcusdt-paper-001
```

`tc drill reconciliation-mismatch` exits non-zero by design when mismatch is detected — this is
the correct outcome, not a command failure.

### Inspect drill artifacts

```bash
ls artifacts/runs/2026-05-20-btcusdt-paper-001/drills/
```

Each drill writes one JSON file:

- `drills/stale_market_data.json` — `outcome=expected_warning`, `pass=true`
- `drills/reconciliation_mismatch.json` — `outcome=expected_mismatch`, `pass=true`
- `drills/restart_recovery.json` — `outcome=simulated_recovery_ok`, `pass=true`

Inspect any drill artifact directly:

```bash
python -m json.tool \
  artifacts/runs/2026-05-20-btcusdt-paper-001/drills/stale_market_data.json
```

Also inspect the reconciliation artifact written by drills and `tc reconcile check`:

```bash
python -m json.tool \
  artifacts/runs/2026-05-20-btcusdt-paper-001/reconciliation_result.json
```

### View drill and reconciliation metrics

One-shot inspection (optional):

```bash
tc metrics export \
  --run-id 2026-05-20-btcusdt-paper-001 \
  --artifacts-root artifacts/runs \
  | grep -E "failure_drill|reconciliation"
```

Expected metrics from Unit 2:

- `tradingchassis_ops_lab_failure_drill_executed_total{run_id=..., drill_name=...} 1`
- `tradingchassis_ops_lab_failure_drill_last_pass{run_id=..., drill_name=...} 1`
- `tradingchassis_ops_lab_failure_drill_last_outcome{run_id=..., drill_name=...} <encoded>`

Existing reconciliation metrics:

- `tradingchassis_ops_lab_reconciliation_status{..., status=warning}` or `{..., status=mismatch}`
- `tradingchassis_ops_lab_reconciliation_checks_total{...}`

### View Grafana panels (Unit 3)

Start the metrics server (if not already running from section 10):

```bash
tc metrics serve \
  --artifacts-root artifacts/runs \
  --evidence-root artifacts/evidence \
  --host 0.0.0.0 \
  --port 8000
```

Start the observability stack (if not already running):

```bash
docker compose -f deploy/observability/docker-compose.yml up
```

In Grafana (`http://localhost:${TC_GRAFANA_PORT:-3000}`), open the
`TradingChassis Ops Lab Run Observability` dashboard and select
`2026-05-20-btcusdt-paper-001` from the `run_id` dropdown.

Confirm three new panels from 0.8.0 (Unit 3):

| Panel | What it shows |
| --- | --- |
| `Reconciliation Status` | Artifact-backed reconciliation status from `reconciliation_result.json`; shows label `warning` or `mismatch` depending on which drill ran last |
| `Failure Drill Last Pass` | Encoded pass/fail per drill; `1`=pass, `0`=fail, `-1`=unknown |
| `Failure Drill Outcome` | Encoded outcome per drill; `1`=expected_warning, `2`=expected_mismatch, `3`=simulated_recovery_ok, `-1`=unknown |

These panels are artifact-backed. They do not stream live trading state.

### When to use runbooks

| Symptom | Runbook |
| --- | --- |
| Grafana shows no data | [Observability no data](runbooks/observability-no-data.md) |
| Evidence compare reports missing or incompatible artifacts | [Evidence compare](runbooks/evidence-compare.md) |
| Paper blocked by kill switch | [Safety gate](runbooks/safety-gate.md) |
| Run artifacts missing or malformed | [Artifact health](runbooks/artifact-health.md) |
| Drill or probe metrics missing | [Observability no data](runbooks/observability-no-data.md) |

Expected artifact locations:

- `artifacts/runs/2026-05-20-btcusdt-paper-001/`
- `artifacts/runs/2026-05-20-btcusdt-paper-001/drills/`
- `reports/sample/`
