# Roadmap

## Purpose

This roadmap defines the next development milestones for `TradingChassis Ops Lab` based on the current repository implementation and documented scope.

It keeps the project local-first and operations-focused around NautilusTrader, aligned to proof-of-skill outcomes for trading infrastructure and operations-oriented roles.
The roadmap describes planned work, while `CHANGELOG.md` records released milestones.

## Current capabilities

- Spec-driven run workflows for `backtest` and `paper` modes via `tc`.
- Deterministic run artifacts under `artifacts/runs/<run_id>/` with metadata, journal, metrics, and report outputs.
- Config hashing and dataset fingerprinting for reproducibility signals.
- Minimal Nautilus smoke backtest integration for one fixture-backed instrument path.
- Paper lifecycle skeleton with deterministic heartbeats and no exchange/testnet connectivity.
- Artifact-driven Prometheus text export plus a Grafana dashboard definition JSON.
- File-based kill switch state/events and file-based reconciliation checks.
- Deterministic failure drills and runbooks for stale data, reconciliation mismatch, and restart/recovery rehearsal.
- Curated sample outputs in `reports/sample/` and a structured MkDocs site.

## Capability gap analysis

### 1) Run control and reproducibility

- **Capability area:** Run control and reproducibility
- **Target capability:** RunSpec
- **Current implementation evidence:** `src/ops_lab/runs/spec.py`; `examples/configs/btcusdt_backtest.yaml`; `examples/configs/btcusdt_paper.yaml`
- **Current status:** implemented
- **Gap:** none for current scope
- **Recommended next step:** keep schema stable and extend only with explicit ADR-backed requirements

- **Capability area:** Run control and reproducibility
- **Target capability:** config hash
- **Current implementation evidence:** `src/ops_lab/runs/hashing.py`; usage in `src/ops_lab/runs/backtest.py` and `src/ops_lab/runs/paper.py`
- **Current status:** implemented
- **Gap:** hash covers config only, not packaged as broader run reproducibility envelope
- **Recommended next step:** define a reproducibility section in metadata docs that explicitly composes config hash + data fingerprint

- **Capability area:** Run control and reproducibility
- **Target capability:** data fingerprint
- **Current implementation evidence:** `src/ops_lab/data/fingerprint.py`; `tc data fingerprint` in `src/ops_lab/cli.py`
- **Current status:** implemented
- **Gap:** fingerprint is generated independently and not linked into run metadata automatically
- **Recommended next step:** document a canonical operator step to carry fingerprint reference into run artifacts

- **Capability area:** Run control and reproducibility
- **Target capability:** artifact contract
- **Current implementation evidence:** `docs/run-model.md`; writes in `src/ops_lab/runs/backtest.py` and `src/ops_lab/runs/paper.py`
- **Current status:** implemented
- **Gap:** no machine-readable contract validation command
- **Recommended next step:** add a docs-only artifact checklist in runbooks used during demo review

- **Capability area:** Run control and reproducibility
- **Target capability:** metadata
- **Current implementation evidence:** `src/ops_lab/runs/metadata.py`; sample outputs in `reports/sample/backtest/metadata.json`
- **Current status:** implemented
- **Gap:** curated samples differ from full runtime payload shape
- **Recommended next step:** document sample-vs-runtime differences in one place to prevent overinterpretation

- **Capability area:** Run control and reproducibility
- **Target capability:** journal
- **Current implementation evidence:** `src/ops_lab/runs/journal.py`; lifecycle event appends in run/drill/reconciliation modules
- **Current status:** implemented
- **Gap:** no explicit journal event taxonomy document
- **Recommended next step:** add a compact event glossary page under docs

- **Capability area:** Run control and reproducibility
- **Target capability:** reports
- **Current implementation evidence:** `src/ops_lab/reports/render.py`; `report.md` generation in run lifecycle modules
- **Current status:** implemented
- **Gap:** report coverage is intentionally minimal and non-analytic
- **Recommended next step:** keep reports operational and add explicit "interpretation limits" section in docs

### 2) Engine integration

- **Capability area:** Engine integration
- **Target capability:** Nautilus smoke backtest
- **Current implementation evidence:** `src/ops_lab/engines/nautilus/backtest.py`; wired by `tc run backtest`
- **Current status:** implemented
- **Gap:** single venue/instrument fixture path
- **Recommended next step:** add one more deterministic fixture scenario while preserving smoke scope

- **Capability area:** Engine integration
- **Target capability:** paper lifecycle skeleton
- **Current implementation evidence:** `src/ops_lab/runs/paper.py`; `docs/backtest-vs-paper.md`
- **Current status:** implemented
- **Gap:** synthetic lifecycle only; no runtime state integration
- **Recommended next step:** strengthen lifecycle observability and reconciliation linkage before any connectivity work

- **Capability area:** Engine integration
- **Target capability:** richer backtest scenarios
- **Current implementation evidence:** no scenario matrix beyond current smoke path
- **Current status:** not implemented
- **Gap:** no structured set of additional deterministic backtest scenarios
- **Recommended next step:** define a small scenario catalog limited to operational lifecycle checks

- **Capability area:** Engine integration
- **Target capability:** paper/testnet connectivity
- **Current implementation evidence:** explicit non-connectivity in `src/ops_lab/runs/paper.py`, `docs/limitations.md`
- **Current status:** not implemented
- **Gap:** no connectivity adapter/runtime
- **Recommended next step:** defer until observability + safety + reconciliation integration milestones are complete

- **Capability area:** Engine integration
- **Target capability:** backtest vs paper comparison
- **Current implementation evidence:** conceptual doc at `docs/backtest-vs-paper.md`
- **Current status:** partial
- **Gap:** no artifact-level comparison command/report
- **Recommended next step:** add docs-driven manual comparison checklist first

### 3) Data layer

- **Capability area:** Data layer
- **Target capability:** synthetic fixture data
- **Current implementation evidence:** fixture-driven prepare workflow in `src/ops_lab/data/prepare.py`
- **Current status:** implemented
- **Gap:** limited to one dataset
- **Recommended next step:** keep one canonical dataset until other operational gaps are closed

- **Capability area:** Data layer
- **Target capability:** data preparation
- **Current implementation evidence:** `tc data prepare` in `src/ops_lab/cli.py`; `docs/quickstart.md`
- **Current status:** implemented
- **Gap:** no validation report beyond successful copy
- **Recommended next step:** add documentation checklist for expected prepared files and counts

- **Capability area:** Data layer
- **Target capability:** data fingerprinting
- **Current implementation evidence:** `src/ops_lab/data/fingerprint.py`; `tc data fingerprint`
- **Current status:** implemented
- **Gap:** no automatic enforcement of fingerprint/spec consistency
- **Recommended next step:** document operator validation step in demo flow

- **Capability area:** Data layer
- **Target capability:** real historical data import
- **Current implementation evidence:** none in `src/ops_lab/data/`
- **Current status:** not implemented
- **Gap:** no importer/pipeline for external historical datasets
- **Recommended next step:** defer until local observability and control loops are stronger

- **Capability area:** Data layer
- **Target capability:** data quality checks
- **Current implementation evidence:** no dedicated data QA module or command
- **Current status:** not implemented
- **Gap:** no explicit quality gate beyond parse/runtime behavior
- **Recommended next step:** add docs-defined QA checklist before code-level QA tooling

- **Capability area:** Data layer
- **Target capability:** local storage layout
- **Current implementation evidence:** documented and used paths under `data/`, `artifacts/`, `runtime/`; `docs/run-model.md`
- **Current status:** implemented
- **Gap:** no formal storage lifecycle/retention guidance
- **Recommended next step:** add retention and cleanup guidance to runbooks

### 4) Observability

- **Capability area:** Observability
- **Target capability:** Prometheus text export
- **Current implementation evidence:** `src/ops_lab/observability/metrics.py`; `tc metrics export`
- **Current status:** implemented
- **Gap:** export is batch/file-driven, not continuous scrape source
- **Recommended next step:** add local-only scrape flow milestone

- **Capability area:** Observability
- **Target capability:** Grafana dashboard JSON
- **Current implementation evidence:** `dashboards/grafana/tradingchassis-ops-lab-run-observability.json`
- **Current status:** implemented
- **Gap:** dashboard is static artifact only
- **Recommended next step:** add provisioning docs and sample datasource wiring

- **Capability area:** Observability
- **Target capability:** local Prometheus/Grafana stack
- **Current implementation evidence:** no `docker-compose` or local stack config in repo
- **Current status:** not implemented
- **Gap:** no runnable local observability stack
- **Recommended next step:** make this the next milestone

- **Capability area:** Observability
- **Target capability:** metrics serve endpoint or scrape flow
- **Current implementation evidence:** no HTTP metrics server in `src/ops_lab/`
- **Current status:** not implemented
- **Gap:** no direct scrape target
- **Recommended next step:** implement local scrape workflow built around exported `.prom` files first

- **Capability area:** Observability
- **Target capability:** dashboard provisioning
- **Current implementation evidence:** dashboard JSON exists but no provisioning manifests
- **Current status:** not implemented
- **Gap:** manual import requirement
- **Recommended next step:** add local provisioning files tied to the local stack

- **Capability area:** Observability
- **Target capability:** alert rules
- **Current implementation evidence:** none in repo
- **Current status:** not implemented
- **Gap:** no alert definition layer
- **Recommended next step:** add minimal local alert rule examples after stack is in place

### 5) Safety and control

- **Capability area:** Safety and control
- **Target capability:** file-based kill switch
- **Current implementation evidence:** `src/ops_lab/safety/kill_switch.py`; `tc kill activate/status/clear`
- **Current status:** implemented
- **Gap:** local file model only
- **Recommended next step:** keep local file model and improve runbook drills around operator behavior

- **Capability area:** Safety and control
- **Target capability:** runtime kill switch checks
- **Current implementation evidence:** no enforcement hooks in run lifecycle paths
- **Current status:** partial
- **Gap:** state exists, but run loop does not gate behavior on kill-switch state
- **Recommended next step:** define integration points in docs before coding checks

- **Capability area:** Safety and control
- **Target capability:** safety guard reports
- **Current implementation evidence:** placeholder `src/ops_lab/safety/guards.py`
- **Current status:** not implemented
- **Gap:** no guard evaluation/report artifacts
- **Recommended next step:** design minimal report contract aligned with current artifact model

- **Capability area:** Safety and control
- **Target capability:** stale data guard
- **Current implementation evidence:** stale freshness appears in reconciliation and stale-data drill only
- **Current status:** partial
- **Gap:** no active runtime guard action
- **Recommended next step:** keep as reconciliation-first signal until runtime guard integration is ready

- **Capability area:** Safety and control
- **Target capability:** order-intent blocking later
- **Current implementation evidence:** no order intent flow in current paper skeleton
- **Current status:** not implemented
- **Gap:** no order path to block
- **Recommended next step:** defer until paper runtime state integration exists

### 6) Reconciliation

- **Capability area:** Reconciliation
- **Target capability:** file-based expected vs observed reconciliation
- **Current implementation evidence:** `src/ops_lab/reconciliation/checks.py`; `tc reconcile check`
- **Current status:** implemented
- **Gap:** fixture/file-driven only
- **Recommended next step:** preserve deterministic file path while improving scenario coverage

- **Capability area:** Reconciliation
- **Target capability:** reconciliation artifacts
- **Current implementation evidence:** writes `reconciliation_result.json` under run artifacts
- **Current status:** implemented
- **Gap:** no artifact schema doc page dedicated to reconciliation output
- **Recommended next step:** add a short reconciliation artifact reference page

- **Capability area:** Reconciliation
- **Target capability:** journal events
- **Current implementation evidence:** `reconciliation_checked` appends in `src/ops_lab/reconciliation/checks.py`
- **Current status:** implemented
- **Gap:** event semantics not formally documented
- **Recommended next step:** include reconciliation events in journal glossary

- **Capability area:** Reconciliation
- **Target capability:** metrics export integration
- **Current implementation evidence:** reconciliation metrics emitted in `src/ops_lab/observability/metrics.py` when result exists
- **Current status:** implemented
- **Gap:** integration depends on manual reconciliation execution
- **Recommended next step:** document expected operator order in demo flow

- **Capability area:** Reconciliation
- **Target capability:** reconciliation against paper runtime state
- **Current implementation evidence:** no paper runtime state source, fixtures only
- **Current status:** not implemented
- **Gap:** no runtime collector feeding observed state
- **Recommended next step:** defer until paper lifecycle moves beyond synthetic heartbeat

- **Capability area:** Reconciliation
- **Target capability:** venue/testnet reconciliation later
- **Current implementation evidence:** explicit no connectivity scope in docs and paper lifecycle
- **Current status:** not implemented
- **Gap:** no venue/testnet state ingestion
- **Recommended next step:** keep deferred behind observability + safety prerequisites

### 7) Failure modes and runbooks

- **Capability area:** Failure modes and runbooks
- **Target capability:** stale market data drill
- **Current implementation evidence:** `tc drill stale-market-data`; `docs/runbooks/stale-market-data.md`
- **Current status:** implemented
- **Gap:** deterministic fixture rehearsal only
- **Recommended next step:** add operator checklist for interpreting warning severity

- **Capability area:** Failure modes and runbooks
- **Target capability:** reconciliation mismatch drill
- **Current implementation evidence:** `tc drill reconciliation-mismatch`; dedicated runbook
- **Current status:** implemented
- **Gap:** no remediation automation
- **Recommended next step:** keep manual-response runbook focus

- **Capability area:** Failure modes and runbooks
- **Target capability:** restart/recovery drill
- **Current implementation evidence:** `tc drill restart-recovery`; runbook explicitly states no process restart
- **Current status:** implemented
- **Gap:** artifact rehearsal only
- **Recommended next step:** expand runbook with clearer restart boundary conditions

- **Capability area:** Failure modes and runbooks
- **Target capability:** disconnect drill later
- **Current implementation evidence:** none
- **Current status:** not implemented
- **Gap:** no connectivity runtime to disconnect
- **Recommended next step:** defer

- **Capability area:** Failure modes and runbooks
- **Target capability:** missing update drill later
- **Current implementation evidence:** none
- **Current status:** not implemented
- **Gap:** no update stream runtime integration
- **Recommended next step:** defer

- **Capability area:** Failure modes and runbooks
- **Target capability:** rate-limit exhaustion drill later
- **Current implementation evidence:** none
- **Current status:** not implemented
- **Gap:** no API-driven connectivity layer
- **Recommended next step:** defer

### 8) Local operations environment

- **Capability area:** Local operations environment
- **Target capability:** Docker Compose
- **Current implementation evidence:** no `docker-compose` file
- **Current status:** not implemented
- **Gap:** no one-command local ops stack
- **Recommended next step:** implement as part of next milestone

- **Capability area:** Local operations environment
- **Target capability:** app container
- **Current implementation evidence:** only `.devcontainer/Dockerfile` for development environment
- **Current status:** partial
- **Gap:** no runtime/demo app container definition
- **Recommended next step:** define minimal container for local observability demo flow

- **Capability area:** Local operations environment
- **Target capability:** Prometheus
- **Current implementation evidence:** no Prometheus config or service files
- **Current status:** not implemented
- **Gap:** no local collector deployment
- **Recommended next step:** add local Prometheus config focused on artifact-derived metrics flow

- **Capability area:** Local operations environment
- **Target capability:** Grafana
- **Current implementation evidence:** dashboard JSON only
- **Current status:** partial
- **Gap:** no running Grafana service setup
- **Recommended next step:** add local Grafana service with preloaded dashboard

- **Capability area:** Local operations environment
- **Target capability:** dashboard provisioning
- **Current implementation evidence:** no provisioning manifests
- **Current status:** not implemented
- **Gap:** manual dashboard import
- **Recommended next step:** add datasource/dashboard provisioning in local stack

- **Capability area:** Local operations environment
- **Target capability:** local volumes
- **Current implementation evidence:** runtime paths exist by convention, not stack-managed volumes
- **Current status:** partial
- **Gap:** no explicit volume mapping standards for observability stack
- **Recommended next step:** define named volumes and bind mount policy in docs

- **Capability area:** Local operations environment
- **Target capability:** one-command local ops demo
- **Current implementation evidence:** current flow is multi-command CLI sequence in docs
- **Current status:** not implemented
- **Gap:** no single entrypoint for full observability demo
- **Recommended next step:** provide one documented command flow once local stack exists

### 9) Kubernetes / infrastructure

- **Capability area:** Kubernetes / infrastructure
- **Target capability:** local Kubernetes or MicroK8s
- **Current implementation evidence:** none
- **Current status:** not implemented
- **Gap:** no cluster-based environment
- **Recommended next step:** keep deferred until local ops stack is stable and repeatable

- **Capability area:** Kubernetes / infrastructure
- **Target capability:** manifests / Helm / Kustomize
- **Current implementation evidence:** none
- **Current status:** not implemented
- **Gap:** no deployment packaging
- **Recommended next step:** defer

- **Capability area:** Kubernetes / infrastructure
- **Target capability:** Prometheus/Grafana in cluster
- **Current implementation evidence:** none
- **Current status:** not implemented
- **Gap:** no in-cluster observability stack
- **Recommended next step:** defer

- **Capability area:** Kubernetes / infrastructure
- **Target capability:** GitOps / Argo CD
- **Current implementation evidence:** none
- **Current status:** not implemented
- **Gap:** no GitOps workflow
- **Recommended next step:** defer

- **Capability area:** Kubernetes / infrastructure
- **Target capability:** secrets pattern
- **Current implementation evidence:** no runtime secrets integration in current scope
- **Current status:** not implemented
- **Gap:** no secrets management model
- **Recommended next step:** defer until connectivity scope is explicit

- **Capability area:** Kubernetes / infrastructure
- **Target capability:** run jobs/workflows
- **Current implementation evidence:** none
- **Current status:** not implemented
- **Gap:** no orchestration runtime
- **Recommended next step:** defer

### 10) Documentation and portfolio presentation

- **Capability area:** Documentation and portfolio presentation
- **Target capability:** README
- **Current implementation evidence:** `README.md` includes scope and quickstart
- **Current status:** implemented
- **Gap:** no dedicated roadmap link yet
- **Recommended next step:** add one direct link to roadmap page

- **Capability area:** Documentation and portfolio presentation
- **Target capability:** MkDocs site
- **Current implementation evidence:** `mkdocs.yml` plus docs pages/runbooks
- **Current status:** implemented
- **Gap:** roadmap page not yet in nav
- **Recommended next step:** add Roadmap to nav

- **Capability area:** Documentation and portfolio presentation
- **Target capability:** curated sample artifacts
- **Current implementation evidence:** `reports/sample/` with README and representative files
- **Current status:** implemented
- **Gap:** sample payload shapes are intentionally curated and can differ from runtime detail
- **Recommended next step:** keep curation policy explicit and maintain sample provenance notes

- **Capability area:** Documentation and portfolio presentation
- **Target capability:** runbooks
- **Current implementation evidence:** `docs/runbooks/` includes three deterministic drill runbooks
- **Current status:** implemented
- **Gap:** coverage is limited to current local drill set
- **Recommended next step:** expand only when new failure drills are actually implemented

- **Capability area:** Documentation and portfolio presentation
- **Target capability:** roadmap
- **Current implementation evidence:** not previously present as a dedicated page
- **Current status:** not implemented
- **Gap:** no scoped sequencing document tied to repository evidence
- **Recommended next step:** publish this roadmap

- **Capability area:** Documentation and portfolio presentation
- **Target capability:** contribution guide
- **Current implementation evidence:** `CONTRIBUTING.md`
- **Current status:** implemented
- **Gap:** roadmap alignment guidance for contributors is implicit
- **Recommended next step:** reference roadmap in contribution workflow guidance

## Recommended next milestone

### Local observability stack

Why this is next:

- Current repo already has metric export code and a Grafana dashboard artifact.
- The largest practical gap is operating these together as a repeatable local demo.
- This improves operational credibility without expanding into connectivity or production claims.

Milestone scope:

- Local-only metrics scrape flow built from existing artifact-driven metrics export.
- Docker Compose for local Prometheus + Grafana.
- Provisioned datasource and dashboard wiring for `dashboards/grafana/tradingchassis-ops-lab-run-observability.json`.
- Local docs that show end-to-end run + metrics + dashboard verification.

Out of scope for this milestone:

- Exchange/testnet connectivity.
- Production monitoring claims.
- Kubernetes and GitOps.

## Near-term milestones

- **Milestone A: Local observability stack (recommended next)**
  - Demo: run backtest/paper skeleton, export metrics, view dashboard locally.
- **Milestone B: Safety/reconciliation integration hardening**
  - Demo: run lifecycle with documented kill-switch/reconciliation checkpoints and drill evidence.
- **Milestone C: Reproducibility and artifact contract clarity**
  - Demo: reproducibility checklist showing spec/hash/fingerprint/artifact traceability from docs and artifacts.

## Later milestones

- **Milestone D:** broader deterministic backtest scenario set focused on lifecycle behavior.
- **Milestone E:** deeper paper runtime state integration for reconciliation inputs (still local-first).
- **Milestone F:** optional infrastructure extensions only after local stack stability is demonstrated.

## Explicit non-goals

- Building a strategy research platform.
- Building a profitability or alpha demonstration.
- Claiming production-grade reliability or safety.
- Claiming live exchange connectivity before it exists.
- Jumping directly to Kubernetes before local operations maturity.
- Broadening scope into a generic multi-engine trading platform.

## Roadmap decision rules

- Keep milestones small, testable, and independently demoable.
- Prefer local-first operational quality before infrastructure breadth.
- Prefer observability depth before exchange/testnet connectivity.
- Prefer safety and reconciliation integration before any connectivity work.
- Add new capability only when there is repository evidence and a clear proof-of-skill outcome.
- Preserve current scope language discipline: no profitability claims, no production claims, no implied live connectivity.

## Current recommended sequence

1. Establish a runnable local observability stack around existing metrics/dashboard artifacts.
2. Tighten safety and reconciliation operator workflow integration in local runs and drills.
3. Clarify reproducibility contract usage across spec, config hash, and data fingerprint.
4. Expand deterministic scenario coverage only for operational lifecycle learning.
5. Reassess paper runtime state integration readiness.
6. Evaluate optional infrastructure extensions only after local-first milestones are stable.
