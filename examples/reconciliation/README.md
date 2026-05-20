# Reconciliation Fixtures (Slice 9)

These files are local, deterministic fixtures for `tc reconcile check`.
They are referenced by the `README.md` minimal command walkthrough.

Example:

```bash
tc reconcile check \
  --run-id slice9-example-run \
  --expected examples/reconciliation/expected_match.json \
  --observed examples/reconciliation/observed_match.json
```

This reconciliation flow is file-based and report-only.
It does not connect to any exchange, does not read real accounts, and does not auto-activate the kill switch.
