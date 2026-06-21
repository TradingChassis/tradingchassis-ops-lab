# Failure Modes

This page is the authoritative inventory of local operational failure behavior in TradingChassis Ops Lab.

**Scope of this page:**

- Local, deterministic operational failure states only.
- Not production incident response.
- Not live or testnet exchange monitoring.
- Not chaos engineering.
- Not trading performance analysis.
- Not PnL, alpha, or strategy evaluation.

Failure modes here are triggered by local command invocation against artifact files.
They are observable through structured JSON artifacts, `journal.jsonl` events, Prometheus metrics,
and Grafana dashboard signals. Recovery steps are local and do not require exchange connectivity,
account access, or production systems.

For the full artifact contract, see [Run model](run-model.md).
For operational boundaries, see [Scope](scope.md) and [Limitations](limitations.md).
For step-by-step recovery procedures, see [Runbooks](runbooks/stale-market-data.md).

---

## How to read this contract

### Hard failures (exit 1)

A hard failure means the command could not safely proceed:

- Corrupt or unparseable input file (malformed JSON/JSONL/YAML)
- Missing required precondition (run directory not initialized, required file absent)
- Unsafe operation (path traversal in run ID, invalid loopback target)
- I/O error when writing artifacts

Hard failures exit non-zero and print a descriptive message to stderr. No partial artifact is guaranteed.

### Soft failures (exit 0 with structured artifact)

A soft failure means the operation completed and recorded an expected operational gap:

- Missing credentials → `state=missing_credentials` in `connectivity_readiness.json`
- Probe unreachable → `state=probe_unreachable` in `connectivity_probe.json`
- Paper blocked by active kill switch → `status=safety_blocked` in run artifacts
- Evidence missing some artifacts → `comparison_status=missing_artifacts` in evidence JSON

Soft failures exit 0. Full artifacts are written. Metrics and dashboard panels reflect the
recorded state. These outcomes are not errors — they are valid local operational observations.

### `expected_exit_code`

The table below includes an `Expected exit` column. Non-zero exit is part of the operator contract
for certain drills (for example `tc drill reconciliation-mismatch` intentionally exits 1 to confirm
that a mismatch is detected). Do not treat exit-1 drills as command failures — they are the correct
outcome.

### Dashboard values

Grafana panels are artifact-backed. They summarize completed local run artifacts. They do not stream
live trading state, process health, or exchange telemetry. Panel values should be read as local
operational signals derived from file-based artifacts.

---

## Failure mode inventory

### Artifact / run artifact health

| Failure mode | Trigger | Expected exit | Artifact / signal | Journal event | Metric / dashboard signal | Recovery / verification | 0.8.0 status |
|---|---|---:|---|---|---|---|---|
| Missing `metrics.json` | `tc metrics export` for a run without `metrics.json` | 1 | stderr `RunArtifactsFileMissingError` | — | `tc metrics serve` emits Prometheus `#` comment; dashboard shows no data for that run | Re-run the lifecycle command that writes `metrics.json` (backtest or paper) | existing, documented (run-model caveat) |
| Missing `metadata.json` | `tc metrics export`, `tc connectivity readiness/probe`, `tc evidence compare` | 1 (export, connectivity) / 0 (evidence) | stderr or evidence `missing_artifacts` JSON | — | Evidence `comparison_status=missing_artifacts`; serve skips run | Re-initialize run with `tc run init` and repeat lifecycle | existing, partially documented |
| Malformed `metadata.json` | Any command that parses `metadata.json` (export, kill snapshot update, evidence compare) | 1 | stderr `RunArtifactsParseError` or `KillSwitchReadError` | — | Export fails; serve skips with `#` comment | Inspect with `cat artifacts/runs/<run_id>/metadata.json \| python -m json.tool`; re-run lifecycle to regenerate | existing, tested; runbook planned (Unit 4) |
| Malformed `metrics.json` | `tc metrics export`, `tc evidence compare` | 1 | stderr `RunArtifactsParseError` or `EvidenceArtifactsParseError` | — | Export fails; serve skips run with `#` comment | Inspect JSON; re-run backtest or paper lifecycle | existing, tested; runbook planned (Unit 4) |
| Malformed `journal.jsonl` | `tc metrics export` (line parse error), `tc evidence compare` | 1 | stderr with line number; evidence: stderr then no evidence artifact written | — | Export fails; evidence errors before writing artifact | Inspect `journal.jsonl` around reported line number; re-run lifecycle | existing, tested; runbook planned (Unit 4) |
| Missing or malformed `run_spec.yaml` | `tc run init/backtest/paper`, `tc connectivity readiness/probe`, `tc spec validate` | 1 | stderr `RunSpecLoadError` | — | — | Re-run with a valid spec; use `tc spec validate --spec <path>` to check before init | existing, tested; restart-recovery drill checks artifact presence |

### Evidence

| Failure mode | Trigger | Expected exit | Artifact / signal | Journal event | Metric / dashboard signal | Recovery / verification | 0.8.0 status |
|---|---|---:|---|---|---|---|---|
| Missing evidence artifact | `tc metrics serve --evidence-root` when no evidence pairs exist | 0 | No evidence metrics rendered | — | Evidence panels show no data in Grafana | Run `tc evidence compare` first; then restart `tc metrics serve` | existing, documented |
| Malformed evidence JSON | `tc metrics serve --evidence-root` over a corrupted evidence file | 0 | Prometheus `# skipped evidence artifact due to malformed JSON <path>` | — | Affected evidence pair skipped; other pairs still rendered | Inspect evidence JSON; re-run `tc evidence compare` for that pair | existing, tested |
| Missing compared run directories | `tc evidence compare` when one or both run directories are absent | 0 | `backtest_vs_paper_evidence.json` with `comparison_status=missing_artifacts`; evidence MD written | — | `evidence_backtest_vs_paper_status_total{status=missing_artifacts}` incremented | Re-initialize and re-run the missing lifecycle to produce run artifacts | existing, tested; runbook planned (Unit 4) |
| Incompatible backtest/paper modes | `tc evidence compare` when both runs use the same mode (both backtest or both paper) | 0 | Evidence JSON with `comparison_status=incompatible_runs` | — | `evidence_backtest_vs_paper_status_total{status=incompatible_runs}` incremented | Ensure one run is `mode: backtest` and one is `mode: paper`; re-run compare | existing, tested; runbook planned (Unit 4) |
| Invalid evidence run IDs / path traversal | `tc evidence compare` with run IDs containing `..`, `/`, or other unsafe patterns | 1 | stderr `EvidenceWriteError` | — | No evidence artifact written | Use valid run IDs matching the pattern used at `tc run init` | existing, tested |
| Evidence known gaps are high but expected | `tc metrics serve` with accumulated evidence artifacts | 0 | `evidence_known_gaps_total` reflects expected design gaps | — | `Evidence Known Gaps` panel shows non-zero count | High count is expected by design (no PnL, no fill quality, candle-only data, synthetic paper); not an error | existing, by design; documented in demo-flow |

### Safety

| Failure mode | Trigger | Expected exit | Artifact / signal | Journal event | Metric / dashboard signal | Recovery / verification | 0.8.0 status |
|---|---|---:|---|---|---|---|---|
| Kill switch active | `tc kill activate --run-id <id> --reason <text>` | 0 | `runtime/kill_switch/<run_id>.state.json` (`state=active`); `runtime/kill_switch/<run_id>.events.jsonl` | `kill_switch_activated` | `tradingchassis_ops_lab_kill_switch_state{run_id}=2`; Grafana `Kill Switch State` panel | Inspect state file; clear with `tc kill clear --run-id <id> --reason <text>` | existing, tested; runbook planned (Unit 4) |
| Kill switch cleared / absent | `tc kill clear` or no prior activation | 0 | state=cleared / state file absent | `kill_switch_cleared` / — | `kill_switch_state=1` (cleared) or `kill_switch_state=0` (absent) | Normal state; no action required | existing, tested |
| Paper blocked by safety gate | `tc run paper` when kill switch is active for that run ID | 0 | Full run artifacts written with `status=safety_blocked`; `paper_safety_blocked` event in `journal.jsonl`; Safety section in `report.md` | `paper_safety_blocked` | `kill_switch_state=2`; paper metrics include `heartbeat_count=0` | Clear kill switch (`tc kill clear`); use a fresh run ID or re-run paper | existing, tested; runbook planned (Unit 4) |

### Connectivity readiness

| Failure mode | Trigger | Expected exit | Artifact / signal | Journal event | Metric / dashboard signal | Recovery / verification | 0.8.0 status |
|---|---|---:|---|---|---|---|---|
| Missing credentials | `tc connectivity readiness` when required env vars are absent or empty | 0 | `connectivity_readiness.json` with `state=missing_credentials` | `connectivity_readiness_evaluated` | `tradingchassis_ops_lab_connectivity_readiness_state`; Grafana `Connectivity Readiness` panel | Expected local state; set dummy non-empty env vars to reach `configured` state | existing, tested, documented |
| Invalid readiness config | `tc connectivity readiness` when RunSpec `connectivity_readiness` block has validation errors (duplicate env names, invalid format) | 0 | `connectivity_readiness.json` with `state=invalid_config`; `errors` list in artifact | `connectivity_readiness_evaluated` | `tradingchassis_ops_lab_connectivity_readiness_state=3` | Inspect `connectivity_readiness.json` `errors` field; fix RunSpec and re-run | existing, tested; demo-flow note planned |

### Connectivity probe

| Failure mode | Trigger | Expected exit | Artifact / signal | Journal event | Metric / dashboard signal | Recovery / verification | 0.8.0 status |
|---|---|---:|---|---|---|---|---|
| Probe unreachable | `tc connectivity probe` when no local server is listening at target loopback URL | 0 | `connectivity_probe.json` with `state=probe_unreachable` | `connectivity_probe_evaluated` | `tradingchassis_ops_lab_connectivity_probe_state`; Grafana `Connectivity Probe State` | Start a local fake endpoint (`python -m http.server <port> --bind 127.0.0.1`); re-run probe | existing, tested; see [Connectivity probe runbook](runbooks/connectivity-probe-failed.md) Case 2 |
| Probe timeout | `tc connectivity probe` when local endpoint responds slower than `--timeout-ms` | 0 | `connectivity_probe.json` with `state=probe_timeout` | `connectivity_probe_evaluated` | `tradingchassis_ops_lab_connectivity_probe_state` | Increase `--timeout-ms`; verify local endpoint responds | existing, tested; see [runbook](runbooks/connectivity-probe-failed.md) Case 3 |
| Probe HTTP error | `tc connectivity probe` when local endpoint returns non-2xx | 0 | `connectivity_probe.json` with `state=probe_http_error`; `http_status` recorded | `connectivity_probe_evaluated` | `tradingchassis_ops_lab_connectivity_probe_http_status` | Adjust local endpoint to return 2xx; re-run probe | existing, tested; see [runbook](runbooks/connectivity-probe-failed.md) Case 4 |
| Probe unknown / unexpected failure | `tc connectivity probe` when an unexpected local runtime error occurs | 0 | `connectivity_probe.json` with `state=probe_unknown` | `connectivity_probe_evaluated` | `tradingchassis_ops_lab_connectivity_probe_state=-1` | Inspect `connectivity_probe.json` for details; rerun with a known-good loopback target | existing; see [runbook](runbooks/connectivity-probe-failed.md) Case 5 |
| Probe target rejected (hard fail) | `tc connectivity probe` with non-loopback, non-HTTP, or structurally invalid URL | 1 | stderr `ConnectivityProbeInvalidTargetError`; no probe artifact written | — | — | Use `http://127.0.0.1:<port>/...`, `http://localhost:<port>/...`, or `http://[::1]:<port>/...` only | existing, tested; see [runbook](runbooks/connectivity-probe-failed.md) Case 1 |

### Reconciliation / drills

| Failure mode | Trigger | Expected exit | Artifact / signal | Journal event | Metric / dashboard signal | Recovery / verification | 0.8.0 status |
|---|---|---:|---|---|---|---|---|
| Reconciliation mismatch | `tc drill reconciliation-mismatch --run-id <id>` (or `tc reconcile check` with mismatch fixture) | **1** (by design) | `drills/reconciliation_mismatch.json` with `outcome=expected_mismatch`; `reconciliation_result.json` with `status=mismatch` | `failure_drill_executed` (if `journal.jsonl` exists) | `tradingchassis_ops_lab_reconciliation_status{status=mismatch}` (planned Unit 2 for drill metrics); `Reconciliation Status` panel (planned Unit 3) | Exit 1 is expected; confirm `pass=true` in drill JSON; review `checks[]` for mismatch details | existing, tested; drill metrics and dashboard panel planned (Units 2–3) |
| Stale market data drill | `tc drill stale-market-data --run-id <id>` | 0 | `drills/stale_market_data.json` with `outcome=expected_warning`; `reconciliation_result.json` with `status=warning` | `failure_drill_executed` (if `journal.jsonl` exists) | Reconciliation warning metrics (planned Unit 2); `Failure Drill Last Pass` panel (planned Unit 3) | Confirm `pass=true` in drill JSON; review `summary.warning` count; see [runbook](runbooks/stale-market-data.md) | existing, tested; drill metrics and panel planned (Units 2–3) |
| Restart recovery drill | `tc drill restart-recovery --run-id <id>` | 0 | `drills/restart_recovery.json` with `outcome=simulated_recovery_ok` and artifact presence checklist | `failure_drill_executed` (if `journal.jsonl` exists) | Drill pass metric (planned Unit 2) | Confirm `pass=true` and all required artifacts present in `summary`; see [runbook](runbooks/restart-recovery.md) | existing, tested; drill metrics and panel planned (Units 2–3) |
| Existing drill artifacts | Inspect `artifacts/runs/<run_id>/drills/*.json` after running any drill | — | `schema_version`, `drill_name`, `outcome`, `pass`, `checks[]`, `summary`, `limitations[]` in each drill JSON | — | No Prometheus metrics yet (planned Unit 2) | Use `cat artifacts/runs/<run_id>/drills/<drill_name>.json` to inspect outcome | existing (artifact-only); metrics planned (Unit 2) |

### Observability

| Failure mode | Trigger | Expected exit | Artifact / signal | Journal event | Metric / dashboard signal | Recovery / verification | 0.8.0 status |
|---|---|---:|---|---|---|---|---|
| Grafana shows no data | `tc metrics serve` is not running, Prometheus is not scraping, or `metrics.json` prerequisite is missing | — | Grafana panels empty for selected `$run_id` | — | Empty panels; Prometheus targets page shows down state | Verify `tc metrics serve` is running; check Prometheus targets at `/targets`; confirm `metrics.json` exists for selected run | existing behavior; general runbook planned (Unit 4) |
| Prometheus target down | `tc metrics serve` is stopped or unreachable while Prometheus is running | — | Prometheus targets page shows target state as down | — | Dashboard stale or empty | Restart `tc metrics serve`; refresh Prometheus; wait one scrape interval | existing behavior; runbook planned (Unit 4) |
| Metrics serve vs metrics export confusion | Operator uses `tc metrics export` expecting Grafana to update | — | Export writes Prometheus text to stdout or file; does not feed Grafana | — | Dashboard unchanged | Use `tc metrics serve` for Grafana; use `tc metrics export` only for one-shot inspection | existing, documented in quickstart / demo-flow |

---

## Artifact model

`0.8.0` reuses existing artifact locations. No new artifact roots or file types are introduced.

| Artifact type | Location |
|---|---|
| Per-run core artifacts | `artifacts/runs/<run_id>/` |
| Drill artifacts | `artifacts/runs/<run_id>/drills/<drill_name>.json` |
| Reconciliation artifact | `artifacts/runs/<run_id>/reconciliation_result.json` |
| Evidence artifacts | `artifacts/evidence/<backtest_run_id>__<paper_run_id>/` |

The following are **not** introduced in `0.8.0`:

- `artifacts/failures/` root
- `failure_drill.json` file type
- `failure_recovery.json` file type
- New Markdown failure report format (evidence MD is a separate contract)

---

## 0.8.0 scope

`0.8.0 — Expanded Failure Modes` makes existing local operational failure behavior visible,
documented, and recoverable. It does not add a chaos engineering framework, external connectivity,
or new run modes.

### Unit split

| Unit | Goal | Status |
|---|---|---|
| Unit 1 — Failure Mode Contract / Inventory | This page; `docs/failure-modes.md`; MkDocs nav; cross-links; roadmap alignment | in progress |
| Unit 2 — Failure Drill & Reconciliation Metrics | Extend `observability/metrics.py` to render existing drill artifacts as Prometheus metrics | planned |
| Unit 3 — Minimal Dashboard Panels | Add `Reconciliation Status` and `Failure Drill Last Pass` panels to Grafana dashboard | planned |
| Unit 4 — Runbooks / Demo Flow / Changelog | Add runbooks for artifact health, evidence, safety gate, and observability no-data; update demo flow and release docs | planned |

### Deferred from 0.8.0

The following were evaluated and explicitly deferred:

| Deferred item | Reason |
|---|---|
| `missing-update` drill (new command) | Fixture exists; defer to `0.8.1` to keep Unit 1 docs-only and scope minimal |
| `disconnect` drill as separate command | Substantially covered by `probe_unreachable` + existing probe runbook |
| Rate-limit exhaustion drill | No local rate-limit fixture or model; defer until a deterministic fixture contract exists |
| Stale orderbook drill | No orderbook / LOB data in repo; LOB support is explicitly deferred in [Limitations](limitations.md) |
| `tc run verify` / artifact linter | Restart-recovery drill is the minimal precursor; full linter deferred |
| `artifacts/failures/` root | Run-scoped drill artifacts under `drills/*.json` are sufficient |
| Alertmanager integration | Out of scope per [Future work](future-work.md) |
| Kubernetes / GitOps | Out of scope per [Roadmap](roadmap.md) |
| External exchange / testnet probes | Out of scope per [Scope](scope.md) |

---

## See also

- [Run model](run-model.md) — artifact contract and metrics serve vs export
- [Scope](scope.md) — in-scope and out-of-scope implementation boundaries
- [Limitations](limitations.md) — explicit implementation constraints
- [Demo flow](demo-flow.md) — end-to-end walkthrough including safety, reconciliation, and drill steps
- [Backtest vs paper](backtest-vs-paper.md) — evidence workflow and known gaps
- [Runbooks](runbooks/stale-market-data.md) — recovery procedures for drills
- [Connectivity probe runbook](runbooks/connectivity-probe-failed.md) — probe failure cases
