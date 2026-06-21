# Safety Gate

The file-based kill switch gates paper lifecycle runs. When active, `tc run paper` records a
`safety_blocked` outcome and exits 0 with full artifacts written. This is intentional local safety
behavior and is not a command failure.

This runbook covers local file-based safety state only. It is not real order cancellation, position
flattening, or a production safety guarantee.

## Symptoms

- `tc run paper` reports `status=safety_blocked`.
- `journal.jsonl` contains `paper_safety_blocked` and `paper_safety_checked` events.
- `report.md` includes a `## Safety status` section showing blocked state.
- Grafana `Kill Switch State` panel shows value `2` (active).
- Grafana `Paper Heartbeats` panel shows `0`.
- `tc kill status --run-id <run_id>` shows `state=active`.

## Checks

**1. Check kill switch state:**

```bash
tc kill status --run-id <run_id>
```

Expected states: `active`, `cleared`, or `absent` (no state file exists).

**2. Inspect the state file directly:**

```bash
python -m json.tool runtime/kill_switch/<run_id>.state.json
```

**3. Inspect kill switch events:**

```bash
cat runtime/kill_switch/<run_id>.events.jsonl
```

Each line is a JSON event recording activations and clearances.

**4. Confirm paper artifacts reflect blocked state:**

```bash
python -m json.tool artifacts/runs/<run_id>/metadata.json | grep '"status"'
grep "paper_safety" artifacts/runs/<run_id>/journal.jsonl
```

**5. Export metrics to check kill-switch gauge:**

```bash
tc metrics export --run-id <run_id> --artifacts-root artifacts/runs | grep kill_switch
```

Expected when active: `tradingchassis_ops_lab_kill_switch_state{...} 2`

## Recovery

**Clear the kill switch and rerun paper:**

```bash
tc kill clear --run-id <run_id> --reason "cleared for demo"
tc run paper --spec <path>
```

Using a fresh run ID is recommended to avoid artifact collisions from the previously blocked run:

```bash
tc kill clear --run-id <old_run_id> --reason "cleared"
# Update run_id in spec or use a copy with a new run_id
tc run paper --spec <path-with-new-run-id>
```

**To deliberately demonstrate the blocked state (demo flow):**

```bash
tc kill activate --run-id <run_id> --reason "demo block"
tc run paper --spec <path>
# Observe safety_blocked status and paper_safety_blocked journal event
tc kill clear --run-id <run_id> --reason "demo clear"
tc run paper --spec <path>  # or use a fresh run_id
```

See [Demo flow §11](../demo-flow.md#11-runtime-safety-demo-flow-paper) for the full safety demo
sequence.

## Boundaries

- Local file-based kill switch only.
- Does not perform order cancellation or position flattening.
- Does not provide a production safety guarantee.
- Kill switch state is stored under `runtime/kill_switch/`.
- No exchange connectivity involved.
