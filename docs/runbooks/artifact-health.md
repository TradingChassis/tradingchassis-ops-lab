# Artifact Health

Run artifacts are deterministic file-based outputs under `artifacts/runs/<run_id>/`. Missing or
malformed artifacts cause `tc metrics export`, `tc evidence compare`, and related commands to fail
with a descriptive error.

This runbook covers local artifact health only. It is not production data repair, live process
health monitoring, or exchange connectivity.

## Symptoms

- `tc metrics export --run-id <run_id>` exits 1 with `RunArtifactsFileMissingError` or
  `RunArtifactsParseError`.
- `tc metrics serve` emits a Prometheus `#` comment for a run and produces no metrics for it.
- Grafana panels show no data for the selected `$run_id`.
- `tc evidence compare` reports `comparison_status=missing_artifacts` or exits with a parse error.
- A drill command fails referencing a missing or unreadable artifact.

## Checks

**1. Inspect the run directory:**

```bash
ls artifacts/runs/<run_id>/
```

Expected files after a full lifecycle run:

- `metadata.json`
- `metrics.json`
- `journal.jsonl`
- `report.md`
- `run_spec.yaml`

**2. Validate JSON files:**

```bash
python -m json.tool artifacts/runs/<run_id>/metadata.json
python -m json.tool artifacts/runs/<run_id>/metrics.json
```

Each should parse without error. Any parse error pinpoints the corrupt field.

**3. Inspect `journal.jsonl` around the reported line:**

```bash
# Each line is a separate JSON object — inspect the line reported in the error
awk 'NR==<N>' artifacts/runs/<run_id>/journal.jsonl | python -m json.tool
```

Replace `<N>` with the line number from the error message.

**4. Run a metrics export to see the full error:**

```bash
tc metrics export --run-id <run_id> --artifacts-root artifacts/runs
```

The error message names the missing or malformed file.

**5. Inspect drill artifacts if drill metrics are missing:**

```bash
ls artifacts/runs/<run_id>/drills/
python -m json.tool artifacts/runs/<run_id>/drills/<drill_name>.json
```

Malformed drill JSON is skipped by `tc metrics serve` with a Prometheus comment. Valid drill JSON
produces `tradingchassis_ops_lab_failure_drill_*` metrics.

## Recovery

| Problem | Recovery |
|---|---|
| `metadata.json` missing | Re-run: `tc run backtest --spec <path>` or `tc run paper --spec <path>` |
| `metrics.json` missing | Re-run the backtest or paper lifecycle |
| `metadata.json` or `metrics.json` malformed | Re-run the lifecycle; do not hand-edit artifacts as a normal workflow |
| `journal.jsonl` malformed at a specific line | Re-run the lifecycle; or truncate the file before the corrupt line if partially valid and debugging |
| `run_spec.yaml` missing | Re-run `tc run init --spec <path>` with a valid spec file |
| Drill artifact malformed | Re-run the drill: `tc drill <name> --run-id <run_id>` |

Re-running a lifecycle command overwrites the local artifact directory and is always safe for local
dev/demo use.

## Boundaries

- Local artifact health only.
- Not live process health monitoring.
- Not production data repair.
- No exchange connectivity involved.
- For observability no-data scenarios (Prometheus/Grafana), see
  [Observability no data](observability-no-data.md).
