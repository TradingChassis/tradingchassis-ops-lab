# Contributing to ops-lab

## Project scope

`ops-lab` is a local operations lab around NautilusTrader with explicit current-scope boundaries.
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

- `data/`
- `artifacts/runs/`
- `runtime/`

## Documentation and claim policy

Do not introduce claims that exceed project scope:

- No profitability claims.
- No production-grade safety claims.
- No live exchange connectivity claims.

## Contribution boundaries

- Keep changes small and intentionally scoped.
- Do not introduce new engine abstractions without an ADR.
- Do not add live trading connectivity without an explicit scope decision.
