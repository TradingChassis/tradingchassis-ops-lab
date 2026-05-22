"""Unit tests for Dev Container local observability integration."""

from __future__ import annotations

import json
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _load_json(path: Path) -> dict:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict)
    return loaded


DOCKER_OUTSIDE_OF_DOCKER_FEATURE = "ghcr.io/devcontainers/features/docker-outside-of-docker:1"


def test_devcontainer_config_enables_docker_and_forwarded_ports() -> None:
    config_path = _repo_root() / ".devcontainer/devcontainer.json"
    config = _load_json(config_path)

    assert config.get("workspaceFolder") == "/workspaces/tradingchassis-ops-lab"

    features = config.get("features")
    assert isinstance(features, dict)
    assert DOCKER_OUTSIDE_OF_DOCKER_FEATURE in features
    assert features[DOCKER_OUTSIDE_OF_DOCKER_FEATURE] == {"moby": False}

    forward_ports = config.get("forwardPorts")
    assert isinstance(forward_ports, list)
    assert set(forward_ports) >= {8000, 9090, 3000}

    assert config.get("postCreateCommand") == 'python -m pip install -e ".[dev]"'


def test_devcontainer_readme_documents_local_observability_workflow() -> None:
    readme_path = _repo_root() / ".devcontainer/README.md"
    content = readme_path.read_text(encoding="utf-8")

    metrics_cmd = "tc metrics serve --artifacts-root artifacts/runs --host 0.0.0.0 --port 8000"
    compose_cmd = "docker compose -f deploy/observability/docker-compose.yml up"

    assert metrics_cmd in content
    assert compose_cmd in content
    assert "Workflow A" in content
    assert "Workflow B" in content
    assert "inside Dev Container" in content
    assert "on host" in content.lower()
    assert "http://localhost:${TC_PROMETHEUS_PORT:-9090}/targets" in content
    assert "http://localhost:${TC_GRAFANA_PORT:-3000}" in content
    assert "tradingchassis_ops_lab_metrics" in content
    assert "--host 0.0.0.0" in content
    assert "docker compose version" in content
    assert "unavailable inside the Dev Container" in content
    assert "socket permission errors" in content
    assert "TC_PROMETHEUS_PORT=9091" in content
    assert "TC_GRAFANA_PORT=3001" in content
