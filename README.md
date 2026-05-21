# ops-lab

## What this project is

`ops-lab` is a local operations lab around NautilusTrader. It focuses on reproducible, spec-driven backtest and paper workflows with deterministic local data preparation, artifact-first observability, and file-based operational controls.

The backtest path is a smoke backtest for lifecycle and artifact validation, not a strategy performance report. The paper path is a lifecycle skeleton with no exchange or testnet connectivity.

## Quickstart

Install, run checks, prepare sample data, run one smoke backtest, and export metrics:

```bash
python -m pip install -e ".[dev]"
scripts/check.sh
tc data prepare --dataset btcusdt-sample
tc data fingerprint --dataset btcusdt-sample
tc run backtest --spec examples/configs/btcusdt_backtest.yaml
tc metrics export --run-id 2026-05-20-btcusdt-backtest-001
```

For the complete operational walkthrough (paper lifecycle, kill switch, reconciliation, and drills), see `Full demo flow`.

## Current capabilities

- Run spec validation and deterministic run identity (`run_id`)
- Local dataset preparation and deterministic fingerprinting
- Nautilus-backed smoke backtest artifact lifecycle
- Paper-mode lifecycle skeleton artifact lifecycle (no connectivity)
- Artifact-driven metrics export for Prometheus text format
- File-based kill switch signal (`activate` / `status` / `clear`)
- File-based reconciliation checks from deterministic fixtures
- Deterministic failure drills with runbooks

## Project scope

- Local-first execution model
- One engine: NautilusTrader
- One example instrument: `BTCUSDT`
- One intentionally simple toy strategy
- Two run modes: `backtest` and `paper`

## Full demo flow

Canonical run IDs used below:
- Backtest: `2026-05-20-btcusdt-backtest-001`
- Paper: `2026-05-20-btcusdt-paper-001`

How to choose `<run_id>`:
- Read `run_id` from the spec file under `examples/configs/`, or
- Inspect `artifacts/runs/<run_id>/` and use an existing run directory name.

### 1) Setup

```bash
python -m pip install -e ".[dev]"
scripts/check.sh
```

### 2) Prepare and fingerprint local synthetic data

```bash
tc data prepare --dataset btcusdt-sample
tc data fingerprint --dataset btcusdt-sample
```

Expected artifact locations:
- `data/datasets/`
- `data/fingerprints/`

### 3) Run backtest smoke run

```bash
tc run backtest --spec examples/configs/btcusdt_backtest.yaml
```

Expected artifact location:
- `artifacts/runs/2026-05-20-btcusdt-backtest-001/`

### 4) Run paper lifecycle skeleton

```bash
tc run paper --spec examples/configs/btcusdt_paper.yaml
```

Expected artifact location:
- `artifacts/runs/2026-05-20-btcusdt-paper-001/`

### 5) Export metrics

```bash
tc metrics export --run-id 2026-05-20-btcusdt-backtest-001
tc metrics export --run-id 2026-05-20-btcusdt-paper-001 --output artifacts/runs/2026-05-20-btcusdt-paper-001/metrics.prom
```

Expected artifact location:
- `artifacts/runs/<run_id>/`

### 6) Kill switch activate/status/clear

```bash
tc kill activate --run-id 2026-05-20-btcusdt-paper-001 --reason "manual stop"
tc kill status --run-id 2026-05-20-btcusdt-paper-001
tc kill clear --run-id 2026-05-20-btcusdt-paper-001 --reason "manual reset"
```

Expected artifact location:
- `runtime/kill_switch/`

### 7) Reconciliation check

```bash
tc reconcile check --run-id 2026-05-20-btcusdt-paper-001 --expected examples/reconciliation/expected_match.json --observed examples/reconciliation/observed_match.json
```

Expected artifact location:
- `artifacts/runs/2026-05-20-btcusdt-paper-001/`

### 8) Failure drills

```bash
tc drill stale-market-data --run-id 2026-05-20-btcusdt-paper-001
tc drill reconciliation-mismatch --run-id 2026-05-20-btcusdt-paper-001
tc drill restart-recovery --run-id 2026-05-20-btcusdt-paper-001
```

`tc drill reconciliation-mismatch --run-id 2026-05-20-btcusdt-paper-001` is expected to exit non-zero by design when mismatch is detected.

Expected artifact locations:
- `artifacts/runs/2026-05-20-btcusdt-paper-001/`
- `reports/sample/`

## Artifacts

Primary run artifacts are written under `artifacts/runs/<run_id>/`:

- `run_spec.yaml`
- `metadata.json`
- `journal.jsonl`
- `metrics.json`
- `report.md`
- `reconciliation_result.json` (after reconciliation/drill flows)
- `drills/*.json` (after drill commands)
- `metrics.prom` (when exporting to file)

Additional local outputs:

- Prepared dataset under `data/datasets/btcusdt-sample/`
- Dataset fingerprint at `data/fingerprints/btcusdt-sample.fingerprint.json`
- Kill switch state/events under `runtime/kill_switch/`

Curated representative outputs for quick review live in `reports/sample/`.

## How it works

Each run is driven by a RunSpec YAML. Data commands prepare and fingerprint local synthetic data. Run commands generate run artifacts in `artifacts/runs/<run_id>/`, and observability/safety commands read or extend those artifacts.

```text
RunSpec YAML
   |
   v
tc run backtest / tc run paper
   |
   v
artifacts/runs/<run_id>/
   |-- metadata.json
   |-- journal.jsonl
   |-- metrics.json
   |-- report.md
   |
   +--> tc metrics export
   +--> tc reconcile check
   +--> tc drill ...
```

Operational flow details:
- RunSpec YAML defines a run.
- Data commands prepare/fingerprint local synthetic data.
- Run commands create `artifacts/runs/<run_id>/`.
- Artifacts contain metadata, journal, metrics, and reports.
- Observability exports Prometheus text from artifacts.
- Kill switch writes local runtime state.
- Reconciliation compares expected/observed JSON.
- Failure drills create deterministic local drill reports and link to runbooks.

## Repository map

| Path | What to inspect there |
|---|---|
| `src/ops_lab/` | CLI entrypoints and top-level package modules |
| `src/ops_lab/runs/` | Run orchestration and artifact lifecycle logic |
| `src/ops_lab/engines/nautilus/` | NautilusTrader integration and run-mode adapters |
| `src/ops_lab/data/` | Local dataset preparation and fingerprinting commands |
| `src/ops_lab/observability/` | Metrics generation/export logic from run artifacts |
| `src/ops_lab/safety/` | File-based kill switch commands and runtime state handling |
| `src/ops_lab/reconciliation/` | Expected vs observed state checks and result reporting |
| `src/ops_lab/drills/` | Deterministic failure drills and drill artifact writers |
| `examples/configs/` | RunSpec YAML examples for backtest and paper runs |
| `examples/reconciliation/` | Deterministic expected/observed JSON fixtures |
| `fixtures/datasets/` | Local synthetic dataset fixtures used in demo workflows |
| `reports/sample/` | Curated sample outputs for quick portfolio review |
| `docs/runbooks/` | Failure drill runbooks and operator guidance |
| `dashboards/grafana/` | Static dashboard JSON for run observability |
| `scripts/check.sh` | Repository checks used in local validation |

## Limitations

- Local-first lab; no live exchange connectivity
- Smoke backtest and skeleton paper lifecycle only
- File-based kill switch, reconciliation, and drills
- Single engine and example instrument scope
- No profitability, alpha, latency, or production safety claims

See `docs/limitations.md` for the canonical list.

## Future work

Future work remains intentionally scoped: broaden data/instrument coverage, deepen observability ergonomics, and harden operational workflows while preserving explicit scope boundaries and non-production claims.
