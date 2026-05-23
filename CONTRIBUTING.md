# Contributing to TradingChassis Ops Lab

## Project scope

`TradingChassis Ops Lab` is a local operations lab around NautilusTrader with explicit current-scope boundaries.
Contributions must preserve local-first behavior and the documented non-production scope.

## Local setup

```bash
python -m pip install -e ".[dev]"
```

## Run checks

Use the repository check script before opening a pull request:

```bash
scripts/check.sh
```

## Branch and pull request workflow

- Create a focused branch for one small change set.
- Keep changes small and reviewable.
- Include a clear PR description with scope, constraints, and validation steps.
- Prefer follow-up PRs over broad refactors.

## Runtime artifact policy

Do not commit generated runtime artifacts:

- `/data/` — local prepared datasets and fingerprints (ignored)
- `/artifacts/runs/` — generated run outputs (ignored)
- `runtime/` — local runtime state (ignored)

Source helpers for dataset prepare/fingerprint live in `src/tradingchassis_ops_lab/data/` and are tracked.

## Documentation and claim policy

Do not introduce claims that exceed project scope:

- No profitability claims.
- No production-grade safety claims.
- No live exchange connectivity claims.

## Contribution boundaries

- Keep changes small and intentionally scoped.
- Do not introduce new engine abstractions without an ADR.
- Do not add live trading connectivity without an explicit scope decision.
