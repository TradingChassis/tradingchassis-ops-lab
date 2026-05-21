#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "⚡ Checking formatting..."
ruff format --check .

echo "⚡ Running lint..."
ruff check .

echo "🧪 Running tests..."
python -m pytest

echo "✅ All checks passed!"
