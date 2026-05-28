# Changelog

All notable changes to `TradingChassis Ops Lab` are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.0]

### Added

- Grafana connectivity readiness dashboard panel: `Connectivity Readiness`.
- Local loopback-only connectivity probe command:
  - `tc connectivity probe --spec <path> --url <loopback-url> [--timeout-ms <int>]`
- Deterministic probe artifact output: `artifacts/runs/<run_id>/connectivity_probe.json`.
- Metadata probe summary patch under `metadata["connectivity_probe"]`.
- Journal event append: `connectivity_probe_evaluated`.
- Report probe section update behavior when `report.md` already exists.
- Artifact-backed probe Prometheus metrics:
  - `tradingchassis_ops_lab_connectivity_probe_state`
  - `tradingchassis_ops_lab_connectivity_probe_performed`
  - `tradingchassis_ops_lab_connectivity_probe_latency_seconds`
  - `tradingchassis_ops_lab_connectivity_probe_http_status`
- Grafana probe panels:
  - `Connectivity Probe State`
  - `Connectivity Probe Latency`
- Local probe docs/demo flow updates for loopback probe workflow and artifact inspection.
- Connectivity probe failure runbook: `docs/runbooks/connectivity-probe-failed.md`.

### Changed

- Clarified docs wording that `binance` / `binance_testnet` are RunSpec venue labels and do not imply active external connectivity.
- Expanded Quickstart and Demo Flow with local loopback probe workflow and artifact inspection path.
- Clarified probe metrics caveat: `tc metrics export` still requires `metrics.json`; init+probe alone does not create it.

### Notes

- `0.6.0` is the local loopback connectivity probe milestone.
- Probe is local-only and loopback-only; no real Binance/testnet/live connectivity is included.
- No non-loopback network access is included.
- Probe remains read-only and does not submit/cancel/flatten orders.
- No account/balance/position fetching is included.
- No signed endpoint handling is included.
- No credential validation is included.
- Probe artifacts/metadata/journal/report and probe metrics do not store response body.
- No adapter framework is included.
- No Kubernetes/GitOps work is included.

## [0.5.0]

### Added

- RunSpec `connectivity_readiness` contract block for local-only readiness metadata.
- Validation for readiness placeholder env names, duplicate/overlap placeholders, and readiness venue matching top-level venue.
- Local readiness command: `tc connectivity readiness --spec <path>`.
- Local readiness states:
  - `disabled`
  - `missing_credentials`
  - `configured`
  - `invalid_config`
  - `unknown`
- Readiness artifact output: `artifacts/runs/<run_id>/connectivity_readiness.json`.
- Metadata readiness summary patch under `metadata["connectivity_readiness"]`.
- Journal event append: `connectivity_readiness_evaluated`.
- Report readiness section update behavior when `report.md` already exists.
- Artifact-backed readiness Prometheus metrics:
  - `tradingchassis_ops_lab_connectivity_readiness_state`
  - `tradingchassis_ops_lab_connectivity_readiness_enabled`
  - `tradingchassis_ops_lab_connectivity_readiness_missing_required_env_total`
  - `tradingchassis_ops_lab_connectivity_readiness_probe_performed`

### Notes

- Readiness is local preflight only; no network calls are performed.
- Env var values are never stored in readiness artifacts, metadata, journal, reports, or metrics output.
- Readiness metrics do not expose env var names.
- `tc metrics export` still requires `metrics.json`; readiness-only `tc run init` + `tc connectivity readiness` runs do not create `metrics.json`.
- No exchange/testnet/live connectivity is included.
- No provider API calls are included.
- No real credential validation is included.
- No account/balance/position fetching is included.
- No order submission/cancel/flatten behavior is included.
- No external reconciliation is included.
- No adapter framework is included.
- No dashboard/alerting expansion is included.
- No Kubernetes/GitOps work is included.

## [0.4.0]

### Added

- Built-in Nautilus demo scenario for local backtest runs: `ops_smoke_demo`.
- Hardcoded scenario registry with clear validation failure for unknown scenario names.
- Scenario execution facts in run artifacts (`metadata.json`, `metrics.json`, `journal.jsonl`, `report.md`).
- Artifact-backed Prometheus scenario metrics derived from `metrics.json`:
  - `tradingchassis_ops_lab_backtest_scenario_strategy_registered`
  - `tradingchassis_ops_lab_backtest_scenario_bars_seen_total`
  - `tradingchassis_ops_lab_backtest_scenario_orders_submitted_total`
  - `tradingchassis_ops_lab_backtest_scenario_fills_total`
  - `tradingchassis_ops_lab_backtest_scenario_deterministic_action_triggered`

### Changed

- Renamed example RunSpec scenario identity from `toy_mean_reversion` to `ops_smoke_demo` to avoid implying a real alpha strategy implementation.
- Clarified RunSpec strategy contract: `strategy.name` / `strategy.version` are scenario identity and traceability metadata in current scope.
- Updated README, quickstart, demo flow, run model, and roadmap wording for the built-in local scenario behavior and metrics verification path.

### Notes

- No dynamic custom strategy loading/plugin framework is included.
- No strategy parameters, optimization, or parameter sweeps are included.
- `ops_smoke_demo` does not submit orders (`orders_submitted = 0`, `fills_count = 0`).
- No PnL/Sharpe/returns/profitability/alpha metrics are included.
- No orderbook/L2 support is included.
- No exchange/testnet/live connectivity is included.

## [0.3.0]

### Added

- Artifact-backed runtime safety snapshot integration for kill-switch state in run metadata.
- Kill-switch state metric export via `tradingchassis_ops_lab_kill_switch_state`.
- Deterministic paper lifecycle safety gate path with `safety_blocked` artifact status when kill switch is active.
- `Safety status` report section for paper lifecycle safety outcomes.
- Grafana `Kill Switch State` panel in the local run observability dashboard.

### Changed

- Demo flow and docs now include explicit active -> blocked -> clear -> normal paper safety walkthrough.
- Roadmap tracking now marks Runtime Safety Integration as completed in `0.3.0`.

### Notes

- No real order cancellation is included.
- No position flattening is included.
- No production safety guarantees are implied.
- No exchange/testnet/live connectivity is included.

## [0.2.0]

### Added

- Local artifact-backed metrics serving via `tc metrics serve` at `/metrics`.
- Local Prometheus + Grafana Compose stack under `deploy/observability/`.
- Provisioned Prometheus datasource and Grafana dashboard wiring for local runs.
- Configurable local observability environment variables:
  - `TC_METRICS_TARGET`
  - `TC_PROMETHEUS_PORT`
  - `TC_GRAFANA_PORT`

### Changed

- Local observability documentation was aligned for Dev-Container-first and host-Compose workflows across `README.md`, quickstart, demo flow, and roadmap.

### Notes

- No live exchange connectivity is included.
- No testnet connectivity is included.
- No production monitoring guarantees are implied.
- No profitability or strategy-performance claims are made.

## [0.1.0]

### Added

- RunSpec validation and run artifact initialization workflow.
- Local synthetic dataset preparation for the fixture-backed demo path.
- Deterministic dataset fingerprint generation.
- Minimal NautilusTrader smoke backtest execution path.
- Paper lifecycle skeleton with no exchange or testnet connectivity.
- Artifact-driven Prometheus text metrics export.
- File-based kill switch state and event workflow.
- File-based reconciliation checks from expected vs observed inputs.
- Deterministic local failure drills with corresponding runbooks.
- Curated sample artifacts for portfolio review.
- MkDocs Material documentation site with GitHub Pages publishing workflow.
- Contribution guardrails in `CONTRIBUTING.md` and repository checks in `scripts/check.sh`.

### Notes

- No live exchange connectivity is included.
- No production trading safety guarantees are implied.
- No profitability or strategy-performance claims are made.
