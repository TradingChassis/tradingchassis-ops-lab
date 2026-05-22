"""Unit tests for local observability stack configuration files."""

from __future__ import annotations

from pathlib import Path

import yaml


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_yaml(path: Path) -> dict:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


_DASHBOARD_DIR = "dashboards/grafana"
_DASHBOARD_FILENAME = "tradingchassis-ops-lab-run-observability.json"
_DASHBOARD_BIND_MOUNT = f"../../{_DASHBOARD_DIR}:/var/lib/grafana/dashboards:ro,z"


def test_observability_stack_files_exist() -> None:
    root = _repo_root()
    dashboard_dir = root / _DASHBOARD_DIR
    dashboard_file = dashboard_dir / _DASHBOARD_FILENAME
    expected = [
        root / "deploy/observability/docker-compose.yml",
        root / "deploy/observability/prometheus/prometheus.yml",
        root / "deploy/observability/grafana/provisioning/datasources/prometheus.yml",
        root / "deploy/observability/grafana/provisioning/dashboards/dashboards.yml",
        dashboard_dir,
        dashboard_file,
    ]
    for path in expected:
        assert path.exists(), f"Expected config or dashboard path to exist: {path}"

    assert dashboard_dir.is_dir(), f"Expected dashboard directory: {dashboard_dir}"
    assert dashboard_file.is_file(), f"Expected dashboard JSON file: {dashboard_file}"
    assert not dashboard_file.is_dir(), (
        f"Dashboard JSON path must be a file, not a directory: {dashboard_file}"
    )


def test_compose_contains_only_prometheus_and_grafana_services() -> None:
    compose_path = _repo_root() / "deploy/observability/docker-compose.yml"
    compose = _load_yaml(compose_path)
    services = compose.get("services")
    assert isinstance(services, dict)
    assert set(services) == {"prometheus", "grafana"}

    prometheus = services["prometheus"]
    grafana = services["grafana"]

    assert prometheus.get("image", "").startswith("prom/prometheus")
    assert grafana.get("image", "").startswith("grafana/grafana")
    assert "127.0.0.1:${TC_PROMETHEUS_PORT:-9090}:9090" in prometheus.get("ports", [])
    assert "127.0.0.1:${TC_GRAFANA_PORT:-3000}:3000" in grafana.get("ports", [])
    assert "host.docker.internal:host-gateway" in prometheus.get("extra_hosts", [])

    assert prometheus.get("entrypoint") == ["/bin/sh", "-ec"]
    command = prometheus.get("command")
    assert isinstance(command, list)
    joined_command = "\n".join(command)
    assert "TC_METRICS_TARGET" in joined_command
    assert "host.docker.internal:8000" in joined_command
    assert "prometheus.yml.template" in joined_command
    assert "/tmp/prometheus.yml" in joined_command

    prometheus_volumes = prometheus.get("volumes", [])
    assert (
        "./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml.template:ro,z"
        in prometheus_volumes
    )

    grafana_volumes = grafana.get("volumes", [])
    assert "./grafana/provisioning:/etc/grafana/provisioning:ro,z" in grafana_volumes
    assert _DASHBOARD_BIND_MOUNT in grafana_volumes


def test_grafana_dashboard_bind_mount_uses_directory_mount() -> None:
    compose_path = _repo_root() / "deploy/observability/docker-compose.yml"
    compose = _load_yaml(compose_path)
    grafana_volumes = compose["services"]["grafana"]["volumes"]
    assert _DASHBOARD_BIND_MOUNT in grafana_volumes

    host_path, container_path, mount_opts = _DASHBOARD_BIND_MOUNT.split(":", 2)
    assert host_path == f"../../{_DASHBOARD_DIR}"
    assert container_path == "/var/lib/grafana/dashboards"
    assert mount_opts == "ro,z"


def test_prometheus_scrapes_host_metrics_endpoint() -> None:
    prometheus_path = _repo_root() / "deploy/observability/prometheus/prometheus.yml"
    config = _load_yaml(prometheus_path)
    scrape_configs = config.get("scrape_configs")
    assert isinstance(scrape_configs, list)
    assert len(scrape_configs) == 1

    scrape_job = scrape_configs[0]
    assert scrape_job.get("job_name") == "tradingchassis_ops_lab_metrics"

    static_configs = scrape_job.get("static_configs")
    assert isinstance(static_configs, list)
    assert static_configs[0].get("targets") == ["__TC_METRICS_TARGET__"]


def test_grafana_datasource_uses_prometheus_service_url() -> None:
    datasource_path = (
        _repo_root() / "deploy/observability/grafana/provisioning/datasources/prometheus.yml"
    )
    config = _load_yaml(datasource_path)
    datasources = config.get("datasources")
    assert isinstance(datasources, list)
    assert len(datasources) == 1

    datasource = datasources[0]
    assert datasource.get("type") == "prometheus"
    assert datasource.get("url") == "http://prometheus:9090"
    assert datasource.get("isDefault") is True


def test_grafana_dashboard_provisioning_uses_expected_path() -> None:
    dashboards_path = (
        _repo_root() / "deploy/observability/grafana/provisioning/dashboards/dashboards.yml"
    )
    config = _load_yaml(dashboards_path)
    providers = config.get("providers")
    assert isinstance(providers, list)
    assert len(providers) == 1

    provider = providers[0]
    options = provider.get("options", {})
    assert options.get("path") == "/var/lib/grafana/dashboards"
