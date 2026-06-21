# Observability No Data

Grafana panels may show no data for several independent reasons. This runbook walks through
systematic checks for each layer: metrics server, Prometheus scrape target, dashboard variable, and
artifact availability.

This runbook covers local artifact-backed observability only. It is not live process health
monitoring or Alertmanager configuration.

## Symptoms

- Grafana panels are blank or show `No data` for the selected `$run_id`.
- Prometheus `/targets` page shows the metrics target as `DOWN` or absent.
- `tc metrics export` produces output but Grafana still shows nothing.
- The `$run_id` dropdown in Grafana is empty.
- Some panels have data while others (evidence, drill, reconciliation) do not.

## Checks

**1. Verify `tc metrics serve` is running:**

```bash
curl -s http://localhost:8000/metrics | head -5
```

If that fails, start the server:

```bash
tc metrics serve \
  --artifacts-root artifacts/runs \
  --evidence-root artifacts/evidence \
  --host 0.0.0.0 \
  --port 8000
```

**2. Check Prometheus scrape target:**

Open `http://localhost:${TC_PROMETHEUS_PORT:-9090}/targets`

Target `tradingchassis_ops_lab_metrics` should show `UP`. If `DOWN`: confirm `tc metrics serve`
is running and wait one scrape interval (~15 s).

**3. Verify the Docker Compose stack is running:**

```bash
docker compose -f deploy/observability/docker-compose.yml ps
```

If not running:

```bash
docker compose -f deploy/observability/docker-compose.yml up
```

**4. Check the `$run_id` dashboard variable:**

Open the Grafana dashboard. In the top-left `run_id` dropdown, select a run ID that corresponds to
existing artifacts under `artifacts/runs/<run_id>/`. If the dropdown is empty, no
`tradingchassis_ops_lab_run_info` metric has been scraped yet — verify steps 1–3 first.

**5. Verify `metrics.json` exists for the selected run:**

```bash
ls artifacts/runs/<run_id>/metrics.json
```

A run initialized with `tc run init` only (without a subsequent backtest or paper lifecycle) does
not produce `metrics.json`. Re-run the backtest or paper lifecycle.

**6. For evidence panels — verify evidence artifacts and `--evidence-root`:**

```bash
ls artifacts/evidence/
```

If empty: run `tc evidence compare --backtest-run-id <id> --paper-run-id <id>` first. Also confirm
`tc metrics serve` is started with `--evidence-root artifacts/evidence`.

**7. For drill and reconciliation panels — verify drill artifacts exist:**

```bash
ls artifacts/runs/<run_id>/drills/
ls artifacts/runs/<run_id>/reconciliation_result.json 2>/dev/null || echo "absent"
```

If absent: run a drill first, for example:

```bash
tc drill stale-market-data --run-id <run_id>
```

**8. Distinguish `tc metrics serve` from `tc metrics export`:**

`tc metrics export` writes Prometheus text to stdout or a file for one-shot inspection. It does not
feed Grafana. Use `tc metrics serve` to expose the `/metrics` endpoint that Prometheus scrapes.

## Recovery

| Problem | Recovery |
|---|---|
| `tc metrics serve` not running | Start it (see Check 1 above) |
| Prometheus target `DOWN` | Restart `tc metrics serve`; wait one scrape interval |
| Docker Compose not running | `docker compose -f deploy/observability/docker-compose.yml up` |
| `$run_id` dropdown empty | Re-run a lifecycle to produce `metrics.json`; wait for Prometheus scrape |
| `metrics.json` missing for run | Re-run `tc run backtest` or `tc run paper` |
| Evidence panels empty | Run `tc evidence compare`; restart `tc metrics serve` with `--evidence-root` |
| Drill / reconciliation panels empty | Run a drill command; confirm drill artifacts exist |
| Reconciliation panel empty | Run `tc reconcile check` or a drill that writes `reconciliation_result.json` |

## Boundaries

- Local artifact-backed observability only.
- Not live process health monitoring.
- Not Alertmanager configuration.
- `tc metrics export` is a debug/inspection tool — it does not feed Grafana.
- Evidence panels require `--evidence-root artifacts/evidence` when starting `tc metrics serve`.
- Drill and reconciliation panels require corresponding artifacts to exist under the selected
  `run_id`.
