# Restart Recovery Drill

## What happened

`tc drill restart-recovery --run-id <run_id>` performs an artifact-based recovery rehearsal by checking run artifact presence.

## Expected behavior

- Command exits `0`.
- Drill report is written to `artifacts/runs/<run_id>/drills/restart_recovery.json`.
- Report includes a checklist summary for required and optional artifacts.
- Report includes: "no process restart performed; this is artifact-based recovery rehearsal".
- If `journal.jsonl` exists, a compact `failure_drill_executed` event is appended.

## How to inspect artifacts

- Open `artifacts/runs/<run_id>/drills/restart_recovery.json`.
- Confirm:
  - `outcome=simulated_recovery_ok`
  - `summary.metadata_present=true`
  - `summary.run_spec_present=true`
  - statement explains no real restart was performed.

## What a real production system would do

- Coordinate supervised process restart.
- Validate warm-start state and downstream connectivity.
- Run post-restart safety checks before re-enabling trading actions.

## What this lab intentionally does not do

- No process orchestration.
- No daemon/supervisor control.
- No background watcher or async recovery loop.
