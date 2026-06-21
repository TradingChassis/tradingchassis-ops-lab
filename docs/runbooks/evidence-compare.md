# Evidence Compare

`tc evidence compare` produces a cross-run operational evidence artifact comparing a backtest run to
a paper run. Various missing or incompatible inputs produce different outcomes — some are errors,
some are expected operational observations.

This runbook covers `tc evidence compare` diagnostics only. It is not PnL/performance analysis,
live/testnet equivalence verification, or production incident response.

## Symptoms

- `tc evidence compare` exits 1 with a path-safety or I/O error.
- Evidence JSON shows `comparison_status=missing_artifacts` or `comparison_status=incompatible_runs`.
- `tc metrics serve --evidence-root artifacts/evidence` shows no evidence metrics.
- Grafana `Backtest vs Paper Evidence Status` or `Evidence Known Gaps` panel shows no data.
- `comparison_status=differences_expected` — this is the expected result for the canonical demo
  path, not a failure.

## Checks

**1. Verify both run directories exist:**

```bash
ls artifacts/runs/<backtest_run_id>/
ls artifacts/runs/<paper_run_id>/
```

Both must contain `metadata.json`, `metrics.json`, and `journal.jsonl`.

**2. Confirm modes differ:**

```bash
python -m json.tool artifacts/runs/<backtest_run_id>/metadata.json | grep '"mode"'
python -m json.tool artifacts/runs/<paper_run_id>/metadata.json | grep '"mode"'
```

One must be `"backtest"`, the other `"paper"`. If both are the same mode, compare produces
`comparison_status=incompatible_runs`.

**3. Inspect any existing evidence artifact:**

```bash
python -m json.tool \
  artifacts/evidence/<backtest_run_id>__<paper_run_id>/backtest_vs_paper_evidence.json
```

Check `comparison_status`, `known_gaps`, and `artifacts_present`.

**4. Rerun compare:**

```bash
tc evidence compare \
  --backtest-run-id <backtest_run_id> \
  --paper-run-id <paper_run_id>
```

## Recovery

| Symptom | Recovery |
|---|---|
| Missing backtest run directory | Re-run: `tc run backtest --spec <path>` |
| Missing paper run directory | Re-run: `tc run paper --spec <path>` |
| `comparison_status=missing_artifacts` | Ensure both runs have `metadata.json`, `metrics.json`, `journal.jsonl`; rerun compare |
| `comparison_status=incompatible_runs` | Ensure one run is `mode: backtest`, the other `mode: paper`; rerun compare |
| Path traversal or invalid run ID error | Use valid run IDs (alphanumeric, hyphens, underscores; no `..` or `/`); rerun |
| Evidence panels empty in Grafana | Start `tc metrics serve --evidence-root artifacts/evidence`; confirm evidence artifact exists |
| `comparison_status=differences_expected` | Expected in the canonical demo path — not an error |
| High `known_gaps` count | Expected by design: no PnL, no fill quality, candle-only data, synthetic paper lifecycle |

## Boundaries

- Operational evidence only.
- Not PnL/performance analysis or trading equivalence verification.
- `differences_expected` and non-zero known-gap counts are normal outcomes in this local demo path.
- No exchange connectivity involved.
- For artifact health issues (missing or malformed run artifacts), see
  [Artifact health](artifact-health.md).
