# Reconciliation Mismatch Drill

## What happened

`tc drill reconciliation-mismatch --run-id <run_id>` runs deterministic local reconciliation with an intentional mismatch fixture.

## Expected behavior

- Command exits non-zero by design (`exit 1`).
- Drill report is written to `artifacts/runs/<run_id>/drills/reconciliation_mismatch.json`.
- Reconciliation status in the report is `mismatch`.
- If `journal.jsonl` exists, a compact `failure_drill_executed` event is appended.

## How to inspect artifacts

- Open `artifacts/runs/<run_id>/drills/reconciliation_mismatch.json`.
- Confirm:
  - `outcome=expected_mismatch`
  - `status=completed`
  - `summary.mismatch >= 1`
- Review `artifacts/runs/<run_id>/reconciliation_result.json` for the mismatch details.

## What a real production system would do

- Quarantine trading actions for the affected account/symbol.
- Escalate alerting and open an incident.
- Require operator acknowledgement and state convergence checks before resuming.

## What this lab intentionally does not do

- No exchange/account API polling.
- No kill switch auto-activation.
- No automatic remediation or production incident workflows.
