# Title

Treat backtest and paper as run modes

## Status

Accepted

## Context

v1 needs to demonstrate operational parity across two practical workflows without expanding into live capital deployment.
Backtest and paper cover historical replay and runtime behavior while keeping risk and scope controlled.

## Decision

Define `backtest` and `paper` as two run modes in one common run model.
Focus v1 on operational consistency across these modes, not live trading with capital.

## Consequences

- Enables shared run specs, metadata, artifacts, and journaling conventions
- Supports comparable safety and reconciliation workflows across both modes
- Excludes live capital execution and related production controls from v1

## Non-goals

- Running live trading with real capital in v1
- Proving strategy profitability from mode parity
- Expanding mode taxonomy beyond backtest and paper in v1
