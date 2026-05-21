# Stale Market Data Drill

## What happened

`tc drill stale-market-data --run-id <run_id>` runs a deterministic local reconciliation using stale freshness fixture timestamps.

## Expected behavior

- Command exits `0`.
- Drill report is written to `artifacts/runs/<run_id>/drills/stale_market_data.json`.
- Reconciliation status in the report is `warning`.
- If `journal.jsonl` exists, a compact `failure_drill_executed` event is appended.

## How to inspect artifacts

- Open `artifacts/runs/<run_id>/drills/stale_market_data.json`.
- Confirm:
  - `outcome=expected_warning`
  - `status=completed`
  - `summary.warning >= 1`
- Optionally inspect `artifacts/runs/<run_id>/reconciliation_result.json` for reconciliation details.

## What a real production system would do

- Validate feed health from multiple channels.
- Trigger alerting and failover logic.
- Gate order placement until freshness recovers.

## What this lab intentionally does not do

- No exchange connectivity.
- No live market data subscription.
- No automatic kill switch trigger.
- No order cancel/flatten actions.
