# Connectivity Probe Failed

Use this runbook when `tc connectivity probe` does not produce the state you expected.

Scope reminder:

- This probe is local-only and loopback-only.
- It is a read-only HTTP `GET` check.
- It does not use exchange/testnet/live connectivity.
- It does not store response body.

## Case 1: Probe target rejected before execution

- **Symptom:** CLI exits non-zero with loopback validation error.
- **Likely cause:** URL is non-loopback, non-HTTP, has userinfo, query string, or fragment.
- **Check command:** `tc connectivity probe --help`
- **Safe next action:** Use `http://127.0.0.1:<port>/...`, `http://localhost:<port>/...`, or `http://[::1]:<port>/...` only.
- **What not to do:** Do not bypass loopback validation or switch to external exchange/testnet endpoints.

## Case 2: `probe_unreachable`

- **Symptom:** Probe runs and writes artifact with `state=probe_unreachable`.
- **Likely cause:** No local server is listening on target host/port.
- **Check command:**

  ```bash
  mkdir -p tmp/probe-server && printf "ok\n" > tmp/probe-server/health
  python -m http.server <port> --bind 127.0.0.1 --directory tmp/probe-server
  ```

- **Safe next action:** Start the local fake endpoint on loopback (serves `health` from a temp directory) and rerun probe against `http://127.0.0.1:<port>/health`.
- **What not to do:** Do not use external internet endpoints as fallback.

## Case 3: `probe_timeout`

- **Symptom:** Probe runs and writes artifact with `state=probe_timeout`.
- **Likely cause:** Local endpoint responds slower than `--timeout-ms`.
- **Check command:** `tc connectivity probe --spec <path> --url <loopback-url> --timeout-ms 2000`
- **Safe next action:** Increase timeout for local fake endpoint testing and retry.
- **What not to do:** Do not add credentials, signed endpoints, or external service dependencies.

## Case 4: `probe_http_error`

- **Symptom:** Probe runs and writes artifact with `state=probe_http_error`.
- **Likely cause:** Local endpoint returned non-2xx response (for example 404/500).
- **Check command:** `tc connectivity probe --spec <path> --url <loopback-url>`
- **Safe next action:** Adjust local endpoint path or server behavior to return expected local 2xx.
- **What not to do:** Do not treat this as exchange/testnet API validation.

## Case 5: `probe_unknown`

- **Symptom:** Probe runs and writes artifact with `state=probe_unknown`.
- **Likely cause:** Unexpected local runtime error while probing.
- **Check command:** inspect `artifacts/runs/<run_id>/connectivity_probe.json`
- **Safe next action:** rerun with known-good local endpoint and capture deterministic repro.
- **What not to do:** Do not add raw exception dumps or secrets to artifacts.

## Case 6: Missing or malformed probe artifacts

- **Symptom:** Expected `connectivity_probe.json` missing or malformed.
- **Likely cause:** Probe command failed before write, or file was modified manually.
- **Check command:** `ls artifacts/runs/<run_id>/` and inspect JSON formatting.
- **Safe next action:** re-run `tc run init` with a fresh run_id, then re-run probe.
- **What not to do:** Do not hand-edit artifacts with secret/debug payloads.

## Case 7: `tc metrics export` does not show probe metrics

- **Symptom:** Probe artifact exists but probe metrics are absent.
- **Likely cause:** `metrics.json` prerequisite missing for probe-only (`run init` + probe) flow.
- **Check command:** `ls artifacts/runs/<run_id>/metrics.json`
- **Safe next action:** use a lifecycle that writes `metrics.json` or add minimal test/dev `metrics.json` fixture for local docs/demo checks.
- **What not to do:** Do not treat missing `metrics.json` as a reason to add external connectivity.

## Case 8: Grafana probe panels show no data

- **Symptom:** `Connectivity Probe State` or `Connectivity Probe Latency` panels are empty.
- **Likely cause:** Missing scrape data for selected run or missing probe metrics due to `metrics.json` prerequisite.
- **Check command:** `tc metrics export --run-id <run_id>`
- **Safe next action:** verify probe artifact + metrics export output first, then confirm selected `run_id` in Grafana.
- **What not to do:** Do not switch to live/external endpoints to populate panels.
