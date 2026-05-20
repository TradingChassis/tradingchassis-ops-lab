# ops-lab

## What this is

`ops-lab` is a local operations lab around NautilusTrader.
It demonstrates a reproducible v1 run model with spec-driven backtest and paper workflows, deterministic local data preparation, artifact-first observability, and file-based operational controls.

The backtest path is a smoke backtest for lifecycle and artifact validation, not a strategy performance report.
The paper path is a lifecycle skeleton with no exchange or testnet connectivity.

## What this is not

- A trading bot
- A strategy research platform
- A production trading system
- A profitability claim
- A live exchange integration
- A custom trading engine

## v1 demo flow

Use one local run to demonstrate data prep, run lifecycle, observability export, file-based safety/reconciliation, and deterministic drills.

1. Prepare and fingerprint dataset
2. Run one smoke backtest and one paper lifecycle skeleton
3. Export metrics from artifacts
4. Toggle kill switch state
5. Run reconciliation check
6. Run deterministic failure drills

Build history note: slices 0-10 established the foundations; this slice focuses on portfolio readability and curated evidence.

## Operational features demonstrated

- Run spec validation and deterministic run identity (`run_id`)
- Local dataset preparation and deterministic fingerprinting
- Nautilus-backed smoke backtest artifact lifecycle
- Paper-mode lifecycle skeleton artifact lifecycle (no connectivity)
- Artifact-driven metrics export for Prometheus text format
- File-based kill switch signal (`activate` / `status` / `clear`)
- File-based reconciliation checks from deterministic fixtures
- Deterministic failure drills with runbooks

## Artifacts produced

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

## Minimal command walkthrough

Install and run from a fresh clone:

```bash
python -m pip install -e ".[dev]"
```

Prepare local sample data:

```bash
tc data prepare --dataset btcusdt-sample
tc data fingerprint --dataset btcusdt-sample
```

Expected outputs:
- `data/datasets/btcusdt-sample/`
- `data/fingerprints/btcusdt-sample.fingerprint.json`

Run smoke backtest:

```bash
tc run backtest --spec examples/configs/btcusdt_backtest.yaml
```

Run paper lifecycle skeleton:

```bash
tc run paper --spec examples/configs/btcusdt_paper.yaml
```

How to choose `<run_id>`:
- Read `run_id` from the spec (`examples/configs/*.yaml`), or
- List directories under `artifacts/runs/` and pick an existing run.

Export metrics from existing artifacts:

```bash
tc metrics export --run-id <run_id>
tc metrics export --run-id <run_id> --output artifacts/runs/<run_id>/metrics.prom
```

Expected output:
- `artifacts/runs/<run_id>/metrics.prom` (when `--output` is used)

Toggle file-based kill switch state:

```bash
tc kill activate --run-id <run_id> --reason "manual stop"
tc kill status --run-id <run_id>
tc kill clear --run-id <run_id> --reason "manual reset"
```

Expected outputs:
- `runtime/kill_switch/<run_id>.state.json`
- `runtime/kill_switch/<run_id>.events.jsonl`

Run reconciliation check:

```bash
tc reconcile check --run-id <run_id> --expected examples/reconciliation/expected_match.json --observed examples/reconciliation/observed_match.json
```

Expected output:
- `artifacts/runs/<run_id>/reconciliation_result.json`

Run deterministic failure drills:

```bash
tc drill stale-market-data --run-id <run_id>
tc drill reconciliation-mismatch --run-id <run_id>
tc drill restart-recovery --run-id <run_id>
```

Important:
- `tc drill reconciliation-mismatch --run-id <run_id>` exits non-zero by design (`exit 1`) when mismatch is detected.

Expected outputs:
- `artifacts/runs/<run_id>/drills/stale_market_data.json`
- `artifacts/runs/<run_id>/drills/reconciliation_mismatch.json`
- `artifacts/runs/<run_id>/drills/restart_recovery.json`

## Repo map

- Scope and boundaries: `docs/scope.md`
- Logical architecture: `docs/architecture.md`
- Run model: `docs/run-model.md`
- Backtest vs paper framing: `docs/backtest-vs-paper.md`
- Canonical limitations: `docs/limitations.md`
- Failure drill runbooks: `docs/runbooks/README.md`
- Reconciliation fixtures: `examples/reconciliation/README.md`
- Sample run specs: `examples/configs/`
- Static Grafana dashboard definition: `dashboards/grafana/ops-lab-run-observability.json`
- Curated portfolio samples: `reports/sample/README.md`

## Limitations

- Local-first lab; no live exchange connectivity
- Smoke backtest and skeleton paper lifecycle only
- File-based kill switch, reconciliation, and drills
- Single engine and example instrument scope for v1
- No profitability, alpha, latency, or production safety claims

See `docs/limitations.md` for the canonical list.

## Brief future work

Future work is intentionally brief: broaden data/instrument coverage, deepen observability ergonomics, and harden operational workflows only after preserving the same explicit scope and non-production claims.
