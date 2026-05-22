# Roadmap

## Purpose

This roadmap describes the planned development direction for `TradingChassis Ops Lab` based on the current repository state and documented scope.

Released milestones are documented in the repository changelog.

`TradingChassis Ops Lab` is a local-first operations lab around NautilusTrader. It is not a commitment to build a production trading system.

For context, see [Architecture](architecture.md), [Run model](run-model.md), [Limitations](limitations.md), [Runbooks](runbooks/stale-market-data.md), and [Demo flow](demo-flow.md).

## Current position

| Area | Current state | Status |
|---|---|---|
| Run control | Spec-driven runs with deterministic artifacts, metadata, journal, and reports | implemented (`0.1.0`) |
| Data workflow | Local synthetic dataset prepare and deterministic fingerprint workflow | implemented (`0.1.0`) |
| Engine paths | Nautilus smoke backtest and bounded paper lifecycle skeleton | implemented (`0.1.0`) |
| Observability | Artifact-driven metrics server, local Prometheus/Grafana Compose stack, and provisioned dashboard | implemented (`0.2.0`) |
| Safety and control | File-based kill switch state/events, paper lifecycle safety gate, and safety visibility in metrics/report/dashboard | implemented (`0.3.0`) |
| Reconciliation | File-based expected vs observed checks with reconciliation artifact output | implemented (`0.1.0`) |
| Runbooks | Deterministic runbooks for stale data, mismatch, and restart recovery | implemented (`0.1.0`) |
| Documentation | MkDocs Material site, demo flow, scope/limitations, roadmap | implemented (`0.1.0`; updated through `0.3.0`) |
| Local ops stack | Runnable local Prometheus/Grafana stack for artifact-backed metrics | implemented (`0.2.0`) |
| Kubernetes/GitOps | No cluster manifests or GitOps workflow in current repository | deferred |

## Capability gap analysis

| Capability area | Current implementation | Gap | Recommended direction |
|---|---|---|---|
| Run control and reproducibility | RunSpec validation, config hash, artifact contract, metadata, journal, and reports are in place (`implemented`) | Data fingerprint is not yet automatically linked into run metadata; event and artifact semantics can be clearer | Keep schema stable; document reproducibility workflow and artifact/journal reference conventions |
| Engine integration | Nautilus smoke backtest and paper lifecycle skeleton exist (`implemented`/`partial`) | Backtest scenarios are narrow; paper path remains synthetic with no connectivity or runtime-state ingestion | Expand deterministic scenario coverage first; defer connectivity to the Paper/Testnet Connectivity Probe milestone now that `0.2.0` and `0.3.0` baselines are delivered |
| Data layer | Fixture-backed prepare and fingerprint are in place (`implemented`) | No real historical import pipeline and no dedicated data quality checks | Preserve local deterministic fixtures now; add QA and import paths only after core ops gaps close |
| Observability | `tc metrics serve` plus local Prometheus/Grafana Compose stack and provisioning are in place (`implemented`) | Alerting and deeper operational rule coverage are not in scope yet | Keep the current local stack stable; add only narrow follow-up hardening post-0.3.0 |
| Safety and control | File-based kill switch is integrated into paper lifecycle state checks with artifact-backed visibility (`implemented`) | Scope intentionally remains local and file-based with no order cancellation/flattening | Keep the deterministic local safety gate stable while documenting boundaries before connectivity work |
| Reconciliation | File-based reconciliation, artifact output, and journal event integration are implemented (`implemented`) | Reconciliation is fixture/file-driven only; no paper runtime-state source | Keep deterministic file path; increase coverage; defer runtime-state reconciliation until paper runtime matures |
| Failure modes and runbooks | Three deterministic drills and runbooks are implemented (`implemented`) | Coverage is limited to current local drill set; no disconnect/missing-update/rate-limit drills | Expand drill catalog incrementally with deterministic local artifacts and runbooks |
| Local operations environment | Dev-Container-first and host-Compose workflows are documented and runnable (`implemented`) | Environment-specific Docker/Podman permissions can still vary by host | Keep workflow guidance explicit and local-first; avoid platform abstraction expansion |
| Kubernetes / infrastructure | No Kubernetes manifests, in-cluster observability, or GitOps (`deferred`) | No cluster operating model yet | Keep deferred until local-first operations patterns are stable and repeatable |
| Documentation and portfolio presentation | README/docs/runbooks/samples/contribution guidance are present (`implemented`) | Dense roadmap details reduce scanability for external readers | Keep evidence and scope discipline, but present roadmap in clearer milestone-oriented structure |

### Area notes

#### Run control and reproducibility

- Implemented now: RunSpec validation, config hash, artifact contract, metadata, journal, reports.
- Open gap: data fingerprint linkage into run artifacts is manual.
- Direction: keep reproducibility explicit and auditable in docs and artifact checklists.

#### Engine integration

- Implemented now: minimal Nautilus smoke backtest and paper lifecycle skeleton.
- Open gap: no paper/testnet connectivity path and limited scenario depth.
- Direction: expand deterministic operational scenarios before connectivity.

#### Data layer

- Implemented now: fixture-backed local preparation and fingerprinting.
- Open gap: no historical import flow and no dedicated quality-check command.
- Direction: keep data workflow deterministic and local while improving QA guidance.

#### Observability

- Implemented now: artifact-backed `tc metrics serve`, local Prometheus/Grafana Compose stack, and provisioning.
- Open gap: alerting and additional panel hardening remain intentionally limited.
- Direction: keep observability local and stable; defer alerting until later milestones.

#### Safety and control

- Implemented now: file-based kill switch, lifecycle gate for paper start, and safety status visibility in artifacts, metrics, and dashboard.
- Open gap: no real order cancellation/flattening and no production-style safety controls by design.
- Direction: preserve local deterministic safety behavior while expanding only after connectivity milestones.

#### Reconciliation

- Implemented now: file-based expected vs observed checks and reconciliation artifact output.
- Open gap: no reconciliation against real paper runtime state.
- Direction: preserve deterministic checks and broaden scenarios first.

#### Failure modes and runbooks

- Implemented now: stale data, mismatch, and restart/recovery drills plus runbooks.
- Open gap: additional operational drills are still planned.
- Direction: add deterministic drills that remain local-first and artifact-driven.

#### Local operations environment

- Implemented now: CLI workflows, artifact outputs, and local observability demo path.
- Open gap: host/container runtime differences can still require local troubleshooting.
- Direction: document the practical path clearly and keep the milestone demo-focused.

#### Kubernetes / infrastructure

- Implemented now: none by design in current scope.
- Open gap: no manifests, in-cluster stack, or GitOps patterns.
- Direction: keep deferred behind local operations maturity.

#### Documentation and portfolio presentation

- Implemented now: strong documentation baseline and curated outputs.
- Open gap: roadmap previously overloaded detailed content in long lists.
- Direction: keep technical honesty while improving scanability and flow.

## Completed milestones

### 0.1.0 Local Run / Artifact / Ops Baseline

Implemented in current repository scope:

- RunSpec validation and spec-driven run initialization
- deterministic run artifact layout
- metadata, journal, metrics, and report artifacts
- local synthetic BTCUSDT dataset preparation
- deterministic dataset fingerprinting
- minimal Nautilus smoke backtest
- bounded paper lifecycle skeleton without exchange/testnet/live connectivity
- file-based kill switch state/events
- file-based reconciliation expected vs observed checks
- deterministic failure drills
- runbooks for local operational failure modes
- MkDocs documentation baseline
- `scripts/check.sh`

Explicitly not included:

- local Prometheus/Grafana stack
- exchange/testnet/live connectivity
- production trading claims
- strategy/alpha/PnL/profitability scope
- Kubernetes/GitOps

### 0.2.0 Local Observability Stack

Implemented in current repository scope:

- `tc metrics serve` for local artifact-backed `/metrics`
- local Prometheus + Grafana Compose stack
- provisioned Prometheus datasource and Grafana dashboard
- local runtime hardening (`TC_METRICS_TARGET`, `TC_PROMETHEUS_PORT`, `TC_GRAFANA_PORT`, SELinux-compatible bind mounts)
- documentation for Dev-Container-first and host-Compose workflows

Explicitly not included:

- exchange/testnet/live connectivity
- production monitoring guarantees
- Kubernetes or GitOps

### 0.3.0 Runtime Safety Integration

Implemented in current repository scope:

- artifact-backed kill-switch safety snapshot in run metadata
- deterministic paper lifecycle block when kill switch is active
- safety status section in reports and safety lifecycle metadata fields
- kill-switch state metric export and Grafana panel visibility
- demo flow/docs updates for blocked and cleared paper paths

Explicitly not included:

- real order cancellation
- position flattening
- production risk engine behavior
- exchange/testnet/live connectivity

## Near-term milestones

### 1. Paper/Testnet Connectivity Probe

Goal:

- Add one controlled paper/testnet connectivity path after local observability and safety integration are in place.

Includes:

- one venue path
- one instrument path
- no real capital
- documented runtime discrepancies

Explicitly not included:

- production live trading claims
- multi-venue execution
- profitability claims

### 2. Expanded Failure Modes

Goal:

- Extend deterministic operational drill coverage.

Includes:

- disconnect drill
- missing update drill
- rate-limit exhaustion drill
- stale orderbook drill

### 3. Kubernetes / GitOps Lab

Goal:

- Move proven local operations patterns into a small Kubernetes/GitOps learning environment.

Includes:

- local Kubernetes or MicroK8s
- manifests or Kustomize/Helm packaging
- Prometheus/Grafana in cluster
- GitOps deployment pattern
- secrets handling pattern

Explicitly not included:

- production deployment claims

## Later possibilities

Intentionally not next:

- richer Nautilus smoke/backtest scenario coverage
- historical data import workflows
- dedicated data quality checks
- reconciliation against paper runtime state
- alert rule coverage expansion
- controlled venue/testnet adapter hardening

## Explicit non-goals

- No strategy alpha roadmap.
- No profitability roadmap.
- No production trading system claim.
- No real capital requirement.
- No generic broad trading platform scope expansion.
- No Kubernetes-first path before local operations patterns are stable.

## Roadmap decision rules

- Local-first before Kubernetes.
- Observability before connectivity.
- Safety and reconciliation integration before live-like execution paths.
- One venue/instrument path before multi-venue expansion.
- Keep milestones small, independently demoable, and reviewable.
- Do not add capability without clear artifact/report/test/doc evidence.

## Current recommended sequence

1. Paper/Testnet Connectivity Probe
2. Expanded Failure Modes
3. Kubernetes / GitOps Lab
