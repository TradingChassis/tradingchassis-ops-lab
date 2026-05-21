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


def test_observability_stack_files_exist() -> None:
    root = _repo_root()
    expected = [
        root / "deploy/observability/docker-compose.yml",
        root / "deploy/observability/prometheus/prometheus.yml",
        root / "deploy/observability/grafana/provisioning/datasources/prometheus.yml",
        root / "deploy/observability/grafana/provisioning/dashboards/dashboards.yml",
        root / "dashboards/grafana/tradingchassis-ops-lab-run-observability.json",
    ]
    for path in expected:
        assert path.exists(), f"Expected config or dashboard file to exist: {path}"


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

    prometheus_volumes = prometheus.get("volumes", [])
    assert "./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro,z" in prometheus_volumes

    grafana_volumes = grafana.get("volumes", [])
    assert "./grafana/provisioning:/etc/grafana/provisioning:ro,z" in grafana_volumes
    assert (
        "../../dashboards/grafana/tradingchassis-ops-lab-run-observability.json:"
        "/var/lib/grafana/dashboards/tradingchassis-ops-lab-run-observability.json:ro,z"
    ) in grafana_volumes


def test_prometheus_scrapes_host_metrics_endpoint() -> None:
    prometheus_path = _repo_root() / "deploy/observability/prometheus/prometheus.yml"
    config = _load_yaml(prometheus_path)
    scrape_configs = config.get("scrape_configs")
    assert isinstance(scrape_configs, list)
    assert len(scrape_configs) == 1

    scrape_job = scrape_configs[0]
    assert scrape_job.get("job_name") == "ops_lab_metrics"

    static_configs = scrape_job.get("static_configs")
    assert isinstance(static_configs, list)
    assert static_configs[0].get("targets") == ["host.docker.internal:8000"]


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
