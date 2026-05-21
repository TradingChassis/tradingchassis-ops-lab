# Roadmap

## Purpose

This roadmap describes the planned development direction for `TradingChassis Ops Lab` based on the current repository state and documented scope.

Released milestones are documented in the repository changelog.

`TradingChassis Ops Lab` is a local-first operations lab around NautilusTrader. It is not a commitment to build a production trading system.

For context, see [Architecture](architecture.md), [Run model](run-model.md), [Limitations](limitations.md), [Runbooks](runbooks/stale-market-data.md), and [Demo flow](demo-flow.md).

## Current position

| Area | Current state | Status |
|---|---|---|
| Run control | Spec-driven runs with deterministic artifacts, metadata, journal, and reports | implemented |
| Data workflow | Local synthetic dataset prepare and deterministic fingerprint workflow | implemented |
| Engine paths | Nautilus smoke backtest and bounded paper lifecycle skeleton | implemented |
| Observability | Artifact-driven Prometheus text export and Grafana dashboard JSON | partial |
| Safety and control | File-based kill switch state/events and deterministic drill support | partial |
| Reconciliation | File-based expected vs observed checks with reconciliation artifact output | implemented |
| Runbooks | Deterministic runbooks for stale data, mismatch, and restart recovery | implemented |
| Documentation | MkDocs Material site, demo flow, scope/limitations, roadmap | implemented |
| Local ops stack | No runnable local Prometheus/Grafana stack yet | planned |
| Kubernetes/GitOps | No cluster manifests or GitOps workflow in current repository | deferred |

## Capability gap analysis

| Capability area | Current implementation | Gap | Recommended direction |
|---|---|---|---|
| Run control and reproducibility | RunSpec validation, config hash, artifact contract, metadata, journal, and reports are in place (`implemented`) | Data fingerprint is not yet automatically linked into run metadata; event and artifact semantics can be clearer | Keep schema stable; document reproducibility workflow and artifact/journal reference conventions |
| Engine integration | Nautilus smoke backtest and paper lifecycle skeleton exist (`implemented`/`partial`) | Backtest scenarios are narrow; paper path remains synthetic with no connectivity or runtime-state ingestion | Expand deterministic scenario coverage first; defer connectivity until observability and safety integration is stronger |
| Data layer | Fixture-backed prepare and fingerprint are in place (`implemented`) | No real historical import pipeline and no dedicated data quality checks | Preserve local deterministic fixtures now; add QA and import paths only after core ops gaps close |
| Observability | Prometheus text export and Grafana dashboard JSON exist (`implemented`/`partial`) | No continuous local scrape target, no runnable local stack, no provisioning, no alert rules | Build a local observability stack next, then add provisioning and local alert examples |
| Safety and control | File-based kill switch is implemented; stale signal appears via reconciliation/drills (`implemented`/`partial`) | Kill switch and guards are not integrated into lifecycle execution logic; guard reports are absent | Integrate safety state into runtime flow and artifacts before any live-like connectivity work |
| Reconciliation | File-based reconciliation, artifact output, and journal event integration are implemented (`implemented`) | Reconciliation is fixture/file-driven only; no paper runtime-state source | Keep deterministic file path; increase coverage; defer runtime-state reconciliation until paper runtime matures |
| Failure modes and runbooks | Three deterministic drills and runbooks are implemented (`implemented`) | Coverage is limited to current local drill set; no disconnect/missing-update/rate-limit drills | Expand drill catalog incrementally with deterministic local artifacts and runbooks |
| Local operations environment | Development container exists; no local runtime stack (`partial`/`planned`) | No one-command local operations demo for Prometheus/Grafana | Add Compose-based local stack with documented setup and dashboard provisioning |
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

- Implemented now: artifact metrics export and dashboard JSON.
- Open gap: no runnable local Prometheus/Grafana stack and no provisioning.
- Direction: establish a local stack as the next milestone.

#### Safety and control

- Implemented now: file-based kill switch and drill-ready safety context.
- Open gap: runtime lifecycle does not yet consume kill-switch state as an execution gate.
- Direction: integrate runtime safety state into lifecycle artifacts and metrics before connectivity work.

#### Reconciliation

- Implemented now: file-based expected vs observed checks and reconciliation artifact output.
- Open gap: no reconciliation against real paper runtime state.
- Direction: preserve deterministic checks and broaden scenarios first.

#### Failure modes and runbooks

- Implemented now: stale data, mismatch, and restart/recovery drills plus runbooks.
- Open gap: additional operational drills are still planned.
- Direction: add deterministic drills that remain local-first and artifact-driven.

#### Local operations environment

- Implemented now: CLI workflows and artifacts for local demonstrations.
- Open gap: no Compose-driven local observability environment.
- Direction: add one-command local operations demo around Prometheus/Grafana.

#### Kubernetes / infrastructure

- Implemented now: none by design in current scope.
- Open gap: no manifests, in-cluster stack, or GitOps patterns.
- Direction: keep deferred behind local operations maturity.

#### Documentation and portfolio presentation

- Implemented now: strong documentation baseline and curated outputs.
- Open gap: roadmap previously overloaded detailed content in long lists.
- Direction: keep technical honesty while improving scanability and flow.

## Recommended next milestone

### Local Observability Stack

This is the next step because it:

- builds directly on existing artifact-driven metrics export and dashboard definitions
- stays local-first and demoable
- improves operational visibility without requiring exchange connectivity
- creates a stable base for safety and reconciliation integration

Suggested scope:

- local metrics scrape flow from exported run metrics
- Docker Compose
- Prometheus
- Grafana
- provisioned datasource and dashboard
- documentation for setup and demonstration flow

Explicitly not included:

- exchange/testnet/live connectivity
- production monitoring claims
- Kubernetes or GitOps

## Near-term milestones

### 1. Local Observability Stack

Goal:

- Make run state visible through a local Prometheus/Grafana setup.

Includes:

- local metrics scrape flow from run artifacts
- Docker Compose
- Prometheus configuration
- Grafana provisioning
- dashboard usage documentation

Explicitly not included:

- production monitoring claims
- Alertmanager integration
- Kubernetes
- exchange connectivity

### 2. Runtime Safety Integration

Goal:

- Connect existing file-based safety state to local run lifecycle behavior.

Includes:

- paper lifecycle checks of kill-switch state
- safety/guard status visibility in artifacts
- safety state surfaced in local metrics/report outputs

Explicitly not included:

- real order cancellation
- position flattening
- production risk engine behavior

### 3. Paper/Testnet Connectivity Probe

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

### 4. Expanded Failure Modes

Goal:

- Extend deterministic operational drill coverage.

Includes:

- disconnect drill
- missing update drill
- rate-limit exhaustion drill
- stale orderbook drill

### 5. Kubernetes / GitOps Lab

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

1. Local Observability Stack
2. Runtime Safety Integration
3. Paper/Testnet Connectivity Probe
4. Expanded Failure Modes
5. Kubernetes / GitOps Lab
