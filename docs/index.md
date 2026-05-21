# ops-lab Documentation

`ops-lab` is a local-first trading operations lab around NautilusTrader. It is built for reproducible, spec-driven `backtest` and `paper` workflows with deterministic local data preparation, artifact-first observability, and file-based operational controls.

## What this project is

- A local operations lab for running and inspecting deterministic workflows
- A repository focused on run lifecycle quality, traceability, and drillability
- A constrained environment for backtest smoke runs and paper lifecycle rehearsal

## What this project is not

- Not a live trading system
- Not a production-grade safety or reliability platform
- Not a strategy-performance or profitability benchmark
- Not connected to live exchanges or testnets

## What you can demonstrate

- Spec validation and deterministic `run_id` flows
- Local dataset preparation and fingerprinting
- Smoke backtest and paper lifecycle skeleton runs
- Metrics export, kill switch controls, reconciliation checks, and failure drills
- Consistent run artifacts under `artifacts/runs/<run_id>/`

## Where to go next

- Start with [Quickstart](quickstart.md)
- Run the full [Demo Flow](demo-flow.md)
- Review [Run Model](run-model.md) and [Architecture](architecture.md)
- Use [Runbooks](runbooks/index.md) for deterministic drill response
- Read scope boundaries in [Scope](scope.md) and [Limitations](limitations.md)
