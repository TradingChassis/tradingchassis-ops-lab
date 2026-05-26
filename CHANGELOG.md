# Changelog

All notable changes to `TradingChassis Ops Lab` are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Renamed example RunSpec scenario identity from `toy_mean_reversion` to `ops_smoke_demo` to avoid implying a real alpha strategy implementation.
- Clarified docs and RunSpec model comments that current `strategy` fields are scenario identity/traceability metadata and do not dynamically load custom strategy code.
- Clarified docs that `data.fingerprint` and `observability.*` are currently metadata/reserved fields, and current lifecycle paths still emit standard artifact sets.
- Roadmap now positions `0.4.0 Local Backtest Scenario / Strategy Contract` before Paper/Testnet Connectivity Probe.
- Backtest now registers one built-in scenario strategy for `strategy.name=ops_smoke_demo`, with deterministic operational counters in artifacts.

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
