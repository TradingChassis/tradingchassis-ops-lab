# Title

Treat backtest and paper as run modes

## Status

Accepted

## Context

The current implementation needs to demonstrate operational parity across two practical workflows without expanding into live capital deployment.
Backtest and paper cover historical replay and runtime behavior while keeping risk and scope controlled.

## Decision

Define `backtest` and `paper` as two run modes in one common run model.
Focus the current implementation on operational consistency across these modes, not live trading with capital.

## Consequences

- Enables shared run specs, metadata, artifacts, and journaling conventions
- Supports comparable safety and reconciliation workflows across both modes
- Excludes live capital execution and related production controls from the current implementation

## Non-goals

- Running live trading with real capital in the current implementation
- Proving strategy profitability from mode parity
- Expanding mode taxonomy beyond backtest and paper in the current implementation
