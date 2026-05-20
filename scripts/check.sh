#!/usr/bin/env bash
set -euo pipefail

echo "🔍 Running import-linter..."
lint-imports --verbose

echo "⚡ Running ruff (check only)..."
ruff check src tests

echo "🧠 Running mypy..."
mypy src tests

echo "🧪 Running pytest..."
python -m pytest

echo "✅ All checks passed!"
