#!/usr/bin/env bash
set -euo pipefail

if [ -d /usr/bin ]; then
  export PATH="/usr/bin:/bin:$PATH"
fi

COMPOSE="${COMPOSE:-docker compose}"
COMPOSE_FILES="${COMPOSE_FILES:--f docker-compose.yml -f docker-compose.volume.yml}"
ROOT_DIR="$(pwd)"
REPORTS_DIR="$ROOT_DIR/reports"

mkdir -p "$REPORTS_DIR"

if command -v cygpath >/dev/null 2>&1; then
  REPORTS_MOUNT="$(cygpath -w "$REPORTS_DIR")"
  SCRIPT_PATH="$(cygpath -w "$ROOT_DIR/scripts/permission_audit.py")"
else
  REPORTS_MOUNT="$REPORTS_DIR"
  SCRIPT_PATH="$ROOT_DIR/scripts/permission_audit.py"
fi

echo "Checking local Docker Compose containers..."
$COMPOSE $COMPOSE_FILES ps

echo "Generating read-only permission audit reports..."
MSYS_NO_PATHCONV=1 $COMPOSE $COMPOSE_FILES run --rm \
  -v "${REPORTS_MOUNT}:/app/reports" \
  -v "${SCRIPT_PATH}:/app/scripts/permission_audit.py:ro" \
  web python /app/scripts/permission_audit.py

echo "Reports generated:"
echo "- reports/permission-audit.json"
echo "- reports/permission-audit.md"
