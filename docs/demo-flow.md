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

## 6) Kill switch activate/status/clear

```bash
tc kill activate --run-id 2026-05-20-btcusdt-paper-001 --reason "manual stop"
tc kill status --run-id 2026-05-20-btcusdt-paper-001
tc kill clear --run-id 2026-05-20-btcusdt-paper-001 --reason "manual reset"
```

Expected artifact location:

- `runtime/kill_switch/`

## 7) Reconciliation check

```bash
tc reconcile check --run-id 2026-05-20-btcusdt-paper-001 --expected examples/reconciliation/expected_match.json --observed examples/reconciliation/observed_match.json
```

Expected artifact location:

- `artifacts/runs/2026-05-20-btcusdt-paper-001/`

## 8) Failure drills

```bash
tc drill stale-market-data --run-id 2026-05-20-btcusdt-paper-001
tc drill reconciliation-mismatch --run-id 2026-05-20-btcusdt-paper-001
tc drill restart-recovery --run-id 2026-05-20-btcusdt-paper-001
```

`tc drill reconciliation-mismatch --run-id 2026-05-20-btcusdt-paper-001` is expected to exit non-zero by design when mismatch is detected.

Expected artifact locations:

- `artifacts/runs/2026-05-20-btcusdt-paper-001/`
- `reports/sample/`
