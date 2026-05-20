# Title

Use NautilusTrader as the sole v1 engine

## Status

Accepted

## Context

`ops-lab` is an operations-focused project with finite scope.
v1 needs a stable engine base to demonstrate reproducible runs, metadata, artifacts, safety checks, and failure drills without building core execution infrastructure from scratch.

## Decision

Use NautilusTrader as the only trading engine in v1.
Do not build a custom trading engine.

## Consequences

- Reduces engineering surface area and keeps v1 delivery finite
- Centers effort on operational workflow behavior instead of engine internals
- Constrains engine flexibility in v1 by design

## Non-goals

- Designing or implementing a new trading engine
- Supporting multiple engines in v1
- Positioning the project as an engine benchmark
