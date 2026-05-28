# TradingChassis Ops Lab Documentation

## What this project is

**TradingChassis Ops Lab** is a local-first **trading infrastructure / operations** lab around [NautilusTrader](https://github.com/nautechsystems/nautilus_trader). It is a **Trading Infrastructure Proof of Skill**: reproducible, spec-driven **backtest** and **paper** workflows with deterministic local data preparation, artifact-first observability, and file-based operational controls.

- A local operations lab for running and inspecting deterministic workflows
- A repository focused on run lifecycle quality, traceability, and drillability
- A constrained environment for Nautilus smoke backtest runs and synthetic paper lifecycle rehearsal

## What this project is not

- Not a live trading system
- Not a production-grade safety or reliability platform
- Not a strategy-performance or profitability benchmark
- Not a strategy alpha or PnL project
- Not connected to live exchanges or testnets

## What it can demonstrate

- Spec validation and deterministic `run_id` flows
- Local dataset preparation and fingerprinting (1-minute OHLCV candles)
- Nautilus smoke backtest and bounded synthetic paper lifecycle skeleton runs
- Metrics export, kill switch controls, reconciliation checks, and failure drills
- Local loopback connectivity readiness/probe workflows with artifact-backed metrics and dashboard panels
- Consistent run artifacts under `artifacts/runs/<run_id>/`

## Where to go next

<div class="ops-grid">
  <a class="ops-card" href="quickstart/">
    <strong>Quickstart</strong>
    Short first-run path for install, checks, data prep, backtest smoke run, and metrics export.
  </a>
  <a class="ops-card" href="demo-flow/">
    <strong>Full demo flow</strong>
    End-to-end operational walkthrough including paper lifecycle, kill switch, reconciliation, and drills.
  </a>
  <a class="ops-card" href="roadmap/">
    <strong>Roadmap</strong>
    Completed milestones (0.1.0 through 0.6.0), gaps, and deferred future work.
  </a>
  <a class="ops-card" href="run-model/">
    <strong>Run model</strong>
    Run spec, artifacts, journal, metadata, and reproducibility concepts.
  </a>
  <a class="ops-card" href="architecture/">
    <strong>Architecture</strong>
    Logical architecture and artifact/safety/reconciliation responsibilities.
  </a>
  <a class="ops-card" href="limitations/">
    <strong>Limitations</strong>
    Canonical current implementation boundaries and non-production scope.
  </a>
  <a class="ops-card" href="runbooks/stale-market-data">
    <strong>Runbooks</strong>
    Deterministic runbooks for stale data, connectivity probe failures, mismatch, and restart recovery.
  </a>
  <a class="ops-card" href="https://github.com/TradingChassis/tradingchassis-ops-lab/tree/main/reports/sample">
    <strong>Sample reports</strong>
    Representative outputs for quick review in the repository.
  </a>
</div>
