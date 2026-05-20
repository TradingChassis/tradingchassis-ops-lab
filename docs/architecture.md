# Architecture (Logical)

This document describes the logical architecture only.
Implementation structure, module internals, and package naming are deferred to later slices.

## Diagram

Run Spec -> Nautilus Run Mode -> Journal/Metadata/Artifacts -> Reports/Observability -> Safety/Reconciliation/Drills

## Responsibilities

### Run Spec

- Defines mode (`backtest` or `paper`) and run intent
- Captures immutable run inputs (configuration and references)
- Serves as the versioned source of truth for a run

### Nautilus Run Mode

- Executes the run in one of two modes: backtest or paper
- Applies the same operational model across both modes where possible
- Produces run lifecycle events for downstream tracking

### Journal / Metadata / Artifacts

- Journal records operational run events and notable actions
- Metadata records identifiers, timestamps, status, and hashes
- Artifacts store outputs in a predictable run-oriented layout

### Reports / Observability

- Reports summarize run outcomes and key checks
- Observability hooks expose basic signals for health and run progress
- Designed for practical inspection, not full production telemetry

### Safety / Reconciliation / Drills

- Safety controls include kill switch behavior
- Reconciliation checks detect expected state mismatches
- Failure drills validate operational response for known scenarios
