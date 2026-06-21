"""Unit tests for local observability stack configuration files."""

from __future__ import annotations

import json
import re
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


def test_grafana_dashboard_queries_use_supported_metric_namespace() -> None:
    dashboard_path = _repo_root() / _DASHBOARD_DIR / _DASHBOARD_FILENAME
    dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))

    panels = dashboard.get("panels", [])
    assert isinstance(panels, list)

    metric_pattern = re.compile(r"tradingchassis_ops_lab_[a-zA-Z0-9_]+")
    referenced_metrics: set[str] = set()
    for panel in panels:
        targets = panel.get("targets", [])
        if not isinstance(targets, list):
            continue
        for target in targets:
            if not isinstance(target, dict):
                continue
            expr = target.get("expr")
            if not isinstance(expr, str):
                continue
            assert re.search(r"(^|[^a-zA-Z0-9_])ops_lab_", expr) is None
            referenced_metrics.update(metric_pattern.findall(expr))

    assert "tradingchassis_ops_lab_kill_switch_state" in referenced_metrics
    assert "tradingchassis_ops_lab_connectivity_readiness_state" in referenced_metrics
    assert "tradingchassis_ops_lab_connectivity_probe_state" in referenced_metrics
    assert "tradingchassis_ops_lab_connectivity_probe_latency_seconds" in referenced_metrics
    assert "tradingchassis_ops_lab_evidence_backtest_vs_paper_status_total" in referenced_metrics
    assert "tradingchassis_ops_lab_evidence_known_gaps_total" in referenced_metrics
    assert "tradingchassis_ops_lab_reconciliation_status" in referenced_metrics
    assert "tradingchassis_ops_lab_failure_drill_last_pass" in referenced_metrics
    assert "tradingchassis_ops_lab_failure_drill_last_outcome" in referenced_metrics
    supported_metrics = {
        "tradingchassis_ops_lab_backtest_bars_processed_total",
        "tradingchassis_ops_lab_backtest_engine_duration_seconds",
        "tradingchassis_ops_lab_backtest_input_candles_total",
        "tradingchassis_ops_lab_connectivity_probe_latency_seconds",
        "tradingchassis_ops_lab_connectivity_probe_state",
        "tradingchassis_ops_lab_connectivity_readiness_state",
        "tradingchassis_ops_lab_evidence_backtest_vs_paper_status_total",
        "tradingchassis_ops_lab_evidence_known_gaps_total",
        "tradingchassis_ops_lab_failure_drill_last_outcome",
        "tradingchassis_ops_lab_failure_drill_last_pass",
        "tradingchassis_ops_lab_journal_event_total",
        "tradingchassis_ops_lab_kill_switch_state",
        "tradingchassis_ops_lab_paper_heartbeat_total",
        "tradingchassis_ops_lab_reconciliation_status",
        "tradingchassis_ops_lab_run_duration_seconds",
        "tradingchassis_ops_lab_run_info",
    }
    assert referenced_metrics <= supported_metrics


def test_grafana_dashboard_contains_connectivity_readiness_panel() -> None:
    dashboard_path = _repo_root() / _DASHBOARD_DIR / _DASHBOARD_FILENAME
    dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))
    panels = dashboard.get("panels", [])
    assert isinstance(panels, list)

    readiness_panel = next(
        (panel for panel in panels if panel.get("title") == "Connectivity Readiness"),
        None,
    )
    assert readiness_panel is not None, "Connectivity Readiness panel must exist."
    assert readiness_panel.get("type") == "stat"

    targets = readiness_panel.get("targets", [])
    assert isinstance(targets, list)
    assert targets and isinstance(targets[0], dict)
    assert (
        targets[0].get("expr")
        == 'tradingchassis_ops_lab_connectivity_readiness_state{run_id="$run_id"}'
    )

    mappings = readiness_panel.get("fieldConfig", {}).get("defaults", {}).get("mappings", [])
    assert isinstance(mappings, list) and mappings
    mapping_options = mappings[0].get("options", {})
    assert mapping_options.get("0", {}).get("text") == "disabled"
    assert mapping_options.get("1", {}).get("text") == "configured"
    assert mapping_options.get("2", {}).get("text") == "missing_credentials"
    assert mapping_options.get("3", {}).get("text") == "invalid_config"
    assert mapping_options.get("-1", {}).get("text") == "unknown"


def test_grafana_dashboard_contains_connectivity_probe_state_panel() -> None:
    dashboard_path = _repo_root() / _DASHBOARD_DIR / _DASHBOARD_FILENAME
    dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))
    panels = dashboard.get("panels", [])
    assert isinstance(panels, list)

    probe_state_panel = next(
        (panel for panel in panels if panel.get("title") == "Connectivity Probe State"),
        None,
    )
    assert probe_state_panel is not None, "Connectivity Probe State panel must exist."
    assert probe_state_panel.get("type") == "stat"

    targets = probe_state_panel.get("targets", [])
    assert isinstance(targets, list)
    assert targets and isinstance(targets[0], dict)
    assert (
        targets[0].get("expr")
        == 'tradingchassis_ops_lab_connectivity_probe_state{run_id="$run_id"}'
    )

    mappings = probe_state_panel.get("fieldConfig", {}).get("defaults", {}).get("mappings", [])
    assert isinstance(mappings, list) and mappings
    mapping_options = mappings[0].get("options", {})
    assert mapping_options.get("1", {}).get("text") == "probe_ok"
    assert mapping_options.get("2", {}).get("text") == "probe_http_error"
    assert mapping_options.get("3", {}).get("text") == "probe_timeout"
    assert mapping_options.get("4", {}).get("text") == "probe_unreachable"
    assert mapping_options.get("-1", {}).get("text") == "probe_unknown"


def test_grafana_dashboard_contains_connectivity_probe_latency_panel() -> None:
    dashboard_path = _repo_root() / _DASHBOARD_DIR / _DASHBOARD_FILENAME
    dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))
    panels = dashboard.get("panels", [])
    assert isinstance(panels, list)

    probe_latency_panel = next(
        (panel for panel in panels if panel.get("title") == "Connectivity Probe Latency"),
        None,
    )
    assert probe_latency_panel is not None, "Connectivity Probe Latency panel must exist."
    assert probe_latency_panel.get("type") == "stat"
    assert probe_latency_panel.get("fieldConfig", {}).get("defaults", {}).get("unit") == "s"

    targets = probe_latency_panel.get("targets", [])
    assert isinstance(targets, list)
    assert targets and isinstance(targets[0], dict)
    assert (
        targets[0].get("expr")
        == 'tradingchassis_ops_lab_connectivity_probe_latency_seconds{run_id="$run_id"}'
    )


def test_grafana_dashboard_excludes_alerting_probe_and_env_name_exposure() -> None:
    dashboard_path = _repo_root() / _DASHBOARD_DIR / _DASHBOARD_FILENAME
    dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))
    panels = dashboard.get("panels", [])
    assert isinstance(panels, list)

    for panel in panels:
        assert "alert" not in panel
        assert "alertThreshold" not in panel

    encoded = json.dumps(dashboard, sort_keys=True)
    assert "tradingchassis_ops_lab_connectivity_readiness_probe_result" not in encoded
    assert "testnet.binance.vision" not in encoded
    assert '"url"' not in encoded
    assert '"response_body"' not in encoded
    assert "required_env" not in encoded
    assert "optional_env" not in encoded
    assert "present_env" not in encoded
    assert "missing_env" not in encoded
    assert "TRADINGCHASSIS_" not in encoded
    assert "pnl" not in encoded.lower()
    assert "sharpe" not in encoded.lower()
    assert "returns" not in encoded.lower()


def test_grafana_dashboard_contains_evidence_status_panel() -> None:
    dashboard_path = _repo_root() / _DASHBOARD_DIR / _DASHBOARD_FILENAME
    dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))
    panels = dashboard.get("panels", [])
    assert isinstance(panels, list)

    evidence_panel = next(
        (panel for panel in panels if panel.get("title") == "Backtest vs Paper Evidence Status"),
        None,
    )
    assert evidence_panel is not None, "Backtest vs Paper Evidence Status panel must exist."
    assert evidence_panel.get("type") == "stat"
    description = evidence_panel.get("description", "")
    assert isinstance(description, str)
    assert "operational evidence only" in description.lower()
    assert "not strategy performance" in description.lower()

    targets = evidence_panel.get("targets", [])
    assert isinstance(targets, list)
    assert targets and isinstance(targets[0], dict)
    assert (
        targets[0].get("expr") == "tradingchassis_ops_lab_evidence_backtest_vs_paper_status_total"
    )


def test_grafana_dashboard_contains_evidence_known_gaps_panel() -> None:
    dashboard_path = _repo_root() / _DASHBOARD_DIR / _DASHBOARD_FILENAME
    dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))
    panels = dashboard.get("panels", [])
    assert isinstance(panels, list)

    evidence_panel = next(
        (panel for panel in panels if panel.get("title") == "Evidence Known Gaps"),
        None,
    )
    assert evidence_panel is not None, "Evidence Known Gaps panel must exist."
    assert evidence_panel.get("type") == "stat"
    targets = evidence_panel.get("targets", [])
    assert isinstance(targets, list)
    assert targets and isinstance(targets[0], dict)
    assert targets[0].get("expr") == "tradingchassis_ops_lab_evidence_known_gaps_total"


def test_grafana_dashboard_contains_reconciliation_status_panel() -> None:
    dashboard_path = _repo_root() / _DASHBOARD_DIR / _DASHBOARD_FILENAME
    dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))
    panels = dashboard.get("panels", [])
    assert isinstance(panels, list)

    panel = next(
        (p for p in panels if p.get("title") == "Reconciliation Status"),
        None,
    )
    assert panel is not None, "Reconciliation Status panel must exist."
    assert panel.get("type") == "stat"

    description = panel.get("description", "")
    assert isinstance(description, str)
    assert (
        "reconciliation_result.json" in description.lower()
        or "reconciliation" in description.lower()
    )
    assert "account" not in description.lower() or "account or balance" in description.lower()

    targets = panel.get("targets", [])
    assert isinstance(targets, list)
    assert targets and isinstance(targets[0], dict)
    assert (
        targets[0].get("expr") == 'tradingchassis_ops_lab_reconciliation_status{run_id="$run_id"}'
    )


def test_grafana_dashboard_contains_failure_drill_last_pass_panel() -> None:
    dashboard_path = _repo_root() / _DASHBOARD_DIR / _DASHBOARD_FILENAME
    dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))
    panels = dashboard.get("panels", [])
    assert isinstance(panels, list)

    panel = next(
        (p for p in panels if p.get("title") == "Failure Drill Last Pass"),
        None,
    )
    assert panel is not None, "Failure Drill Last Pass panel must exist."
    assert panel.get("type") == "stat"

    targets = panel.get("targets", [])
    assert isinstance(targets, list)
    assert targets and isinstance(targets[0], dict)
    assert (
        targets[0].get("expr") == 'tradingchassis_ops_lab_failure_drill_last_pass{run_id="$run_id"}'
    )

    mappings = panel.get("fieldConfig", {}).get("defaults", {}).get("mappings", [])
    assert isinstance(mappings, list) and mappings
    mapping_options = mappings[0].get("options", {})
    assert mapping_options.get("1", {}).get("text") == "pass"
    assert mapping_options.get("0", {}).get("text") == "fail"
    assert mapping_options.get("-1", {}).get("text") == "unknown"


def test_grafana_dashboard_contains_failure_drill_outcome_panel() -> None:
    dashboard_path = _repo_root() / _DASHBOARD_DIR / _DASHBOARD_FILENAME
    dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))
    panels = dashboard.get("panels", [])
    assert isinstance(panels, list)

    panel = next(
        (p for p in panels if p.get("title") == "Failure Drill Outcome"),
        None,
    )
    assert panel is not None, "Failure Drill Outcome panel must exist."
    assert panel.get("type") == "stat"

    targets = panel.get("targets", [])
    assert isinstance(targets, list)
    assert targets and isinstance(targets[0], dict)
    assert (
        targets[0].get("expr")
        == 'tradingchassis_ops_lab_failure_drill_last_outcome{run_id="$run_id"}'
    )

    mappings = panel.get("fieldConfig", {}).get("defaults", {}).get("mappings", [])
    assert isinstance(mappings, list) and mappings
    mapping_options = mappings[0].get("options", {})
    assert mapping_options.get("1", {}).get("text") == "expected_warning"
    assert mapping_options.get("2", {}).get("text") == "expected_mismatch"
    assert mapping_options.get("3", {}).get("text") == "simulated_recovery_ok"
    assert mapping_options.get("-1", {}).get("text") == "unknown"


def test_grafana_dashboard_panel_ids_are_unique() -> None:
    dashboard_path = _repo_root() / _DASHBOARD_DIR / _DASHBOARD_FILENAME
    dashboard = json.loads(dashboard_path.read_text(encoding="utf-8"))
    panels = dashboard.get("panels", [])
    assert isinstance(panels, list)

    ids = [panel.get("id") for panel in panels if isinstance(panel.get("id"), int)]
    assert len(ids) == len(set(ids)), f"Duplicate panel IDs found: {ids}"
