# Title

Use a local-first monorepo for v1

## Status

Accepted

## Context

v1 aims to be easy to run, easy to inspect, and limited in scope.
A local-first monorepo supports simple onboarding and consistent execution for an operations-focused portfolio project.

## Decision

Use a local-first monorepo as the default development and execution model in v1.
Defer distributed deployment complexity and broad platform concerns.

## Consequences

- Improves reproducibility and setup simplicity for contributors and reviewers
- Keeps architecture and operational workflows understandable in a single repository
- Defers scalability and multi-environment concerns to post-v1 work

## Non-goals

- Building a cloud-native platform in v1
- Treating Kubernetes as a required deployment target
- Introducing production multi-cluster operations
