# Dev Container Observability Workflow

Use this local workflow to run the observability stack. This is **not** production monitoring.

## Project setup

After the Dev Container is created, the project is installed in editable mode with dev dependencies:

```bash
python -m pip install -e ".[dev]"
```

If `tc` is not on your PATH, re-run the command above from the repository root.

The metrics server runs inside the Dev Container. Prometheus and Grafana can be started with Compose either inside the Dev Container (Workflow A) or on the host (Workflow B).

## Workflow A: Compose available inside Dev Container (Dev-Container-first)

Terminal 1 (inside Dev Container):

```bash
tc metrics serve --artifacts-root artifacts/runs --host 0.0.0.0 --port 8000
```

Terminal 2 (inside Dev Container):

```bash
TC_METRICS_TARGET=<dev-container-ip>:8000 \
TC_PROMETHEUS_PORT=9091 \
TC_GRAFANA_PORT=3001 \
docker compose -f deploy/observability/docker-compose.yml up
```

Why this is needed: Prometheus defaults to scraping `host.docker.internal:8000`, which is ideal when `tc metrics serve` runs on the host. In a Dev-Container-first workflow, the metrics server runs inside the Dev Container, so `host.docker.internal` can point to the host/gateway instead of the Dev Container.

Find the Dev Container IP before starting Compose:

```bash
hostname -I
```

Use one of the returned IP addresses in `TC_METRICS_TARGET`.

If Workflow A fails with Docker socket permission errors inside the Dev Container, use Workflow B.

## Workflow B: Compose available only on host

Terminal 1 (inside Dev Container):

```bash
tc metrics serve --artifacts-root artifacts/runs --host 0.0.0.0 --port 8000
```

Terminal 2 (**on host, from repository root**):

```bash
docker compose -f deploy/observability/docker-compose.yml up
```

Default target behavior in both workflows:

- `TC_METRICS_TARGET` is optional.
- If omitted, Prometheus still scrapes `host.docker.internal:8000`.

Port conflict examples (run on host):

```bash
TC_PROMETHEUS_PORT=9091 docker compose -f deploy/observability/docker-compose.yml up
TC_GRAFANA_PORT=3001 docker compose -f deploy/observability/docker-compose.yml up
```

## Verification (both workflows, local only)

- Prometheus targets: http://localhost:${TC_PROMETHEUS_PORT:-9090}/targets
- Target `tradingchassis_ops_lab_metrics` should be `UP`
- Grafana: http://localhost:${TC_GRAFANA_PORT:-3000}
- Dashboard is provisioned automatically

`--host 0.0.0.0` is recommended when the metrics server runs inside the Dev Container so Prometheus can reach the forwarded metrics port.

## Diagnostics

Inside the Dev Container:

```bash
docker --version
docker compose version
```

Host port diagnostics:

```bash
ss -ltnp | grep ':9090' || true
ss -ltnp | grep ':3000' || true
```

Container engine checks:

```bash
docker ps
```

Optional on rootless Podman hosts:

```bash
podman ps
```

If `docker compose` is unavailable inside the Dev Container, run the Compose command from the host (Workflow B) instead.

## Notes

- The Dev Container uses `docker-outside-of-docker` with `moby: false` so container CLI commands can talk to your host container engine when available.
- On standard Docker hosts, Workflow A usually works without extra setup.
- On Linux Atomic with rootless Podman, Compose/Podman may be host-managed; Workflow B is acceptable. Set Cursor `dev.containers.dockerPath` to `podman` and ensure the user socket is running:
- Compose bind mounts use SELinux-compatible `:z` labels so Prometheus and Grafana can read local config and provisioning files. If Prometheus still fails with permission denied on `prometheus.yml`, check host file permissions and SELinux labels.

```bash
systemctl --user enable --now podman.socket
```
