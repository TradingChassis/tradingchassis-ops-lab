# TradingChassis Ops Lab

`TradingChassis Ops Lab` is a local-first trading operations lab around [NautilusTrader](https://github.com/nautechsystems/nautilus_trader). It focuses on reproducible, spec-driven backtest and paper workflows with deterministic local data preparation, artifact-first observability, and file-based operational controls.

The backtest path is a smoke backtest for lifecycle and artifact validation, not a strategy performance report. The paper path is a lifecycle skeleton with no exchange or testnet connectivity.

## Quickstart summary

```bash
python -m pip install -e ".[dev]"
scripts/check.sh
tc data prepare --dataset btcusdt-sample
tc data fingerprint --dataset btcusdt-sample
tc run backtest --spec examples/configs/btcusdt_backtest.yaml
tc metrics export --run-id 2026-05-20-btcusdt-backtest-001
```

## Documentation

- Documentation is published with GitHub Pages from the MkDocs site.
- Local docs home: [`docs/index.md`](docs/index.md)
- Local quickstart page: [`docs/quickstart.md`](docs/quickstart.md)
- Local full walkthrough: [`docs/demo-flow.md`](docs/demo-flow.md)

## Scope guardrails

- Local-only operations lab; no live exchange connectivity
- Backtest smoke run and paper lifecycle skeleton only
- No profitability, alpha, production-safety, or low-latency claims
