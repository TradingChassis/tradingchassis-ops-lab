# Quickstart

Install, run checks, prepare sample data, run one smoke backtest, and export metrics.

```bash
python -m pip install -e ".[dev]"
scripts/check.sh
tc data prepare --dataset btcusdt-sample
tc data fingerprint --dataset btcusdt-sample
tc run backtest --spec examples/configs/btcusdt_backtest.yaml
tc metrics export --run-id 2026-05-20-btcusdt-backtest-001
```

Expected artifact locations:

- `data/datasets/`
- `data/fingerprints/`
- `artifacts/runs/2026-05-20-btcusdt-backtest-001/`

For the complete operational walkthrough, continue to [Demo Flow](demo-flow.md).
