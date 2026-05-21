# Title

Use NautilusTrader as the sole engine

## Status

Accepted

## Context

`ops-lab` is an operations-focused project with finite scope.
The current implementation needs a stable engine base to demonstrate reproducible runs, metadata, artifacts, safety checks, and failure drills without building core execution infrastructure from scratch.

## Decision

Use NautilusTrader as the only trading engine in the current implementation.
Do not build a custom trading engine.

## Consequences

- Reduces engineering surface area and keeps delivery finite
- Centers effort on operational workflow behavior instead of engine internals
- Constrains engine flexibility in the current implementation by design

## Non-goals

- Designing or implementing a new trading engine
- Supporting multiple engines in the current implementation
- Positioning the project as an engine benchmark
