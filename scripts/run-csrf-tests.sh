#!/usr/bin/env bash
set -euo pipefail

if [ -d /usr/bin ]; then
  export PATH="/usr/bin:/bin:$PATH"
fi

COMPOSE="${COMPOSE:-docker compose}"
COMPOSE_FILES="${COMPOSE_FILES:--f docker-compose.yml -f docker-compose.volume.yml}"
ROOT_DIR="$(pwd)"

if command -v cygpath >/dev/null 2>&1; then
  TESTS_MOUNT="$(cygpath -w "$ROOT_DIR/tests")"
  PYTEST_INI_MOUNT="$(cygpath -w "$ROOT_DIR/pytest.ini")"
  API_PERMISSION_LOG_REVIEW_MOUNT="$(cygpath -w "$ROOT_DIR/scripts/api_permission_log_review.py")"
else
  TESTS_MOUNT="$ROOT_DIR/tests"
  PYTEST_INI_MOUNT="$ROOT_DIR/pytest.ini"
  API_PERMISSION_LOG_REVIEW_MOUNT="$ROOT_DIR/scripts/api_permission_log_review.py"
fi

echo "Checking Docker Compose containers..."
$COMPOSE $COMPOSE_FILES ps

DB_HEALTH="$($COMPOSE $COMPOSE_FILES ps db 2>/dev/null | grep -c "healthy" || true)"
if [ "$DB_HEALTH" -lt 1 ]; then
  echo "db container is not healthy."
  exit 1
fi

echo "Running CSRF-enabled tests..."
MSYS_NO_PATHCONV=1 ENABLE_CSRF_PROTECTION=True $COMPOSE $COMPOSE_FILES run --rm \
  -v "${TESTS_MOUNT}:/app/tests:ro" \
  -v "${PYTEST_INI_MOUNT}:/app/pytest.ini:ro" \
  -v "${API_PERMISSION_LOG_REVIEW_MOUNT}:/app/scripts/api_permission_log_review.py:ro" \
  -e ENABLE_CSRF_PROTECTION=True \
  -e TEST_USERNAME \
  -e TEST_PASSWORD \
  -e TEST_USERNAME_SECONDARY \
  -e TEST_PASSWORD_SECONDARY \
  -e TEST_ADMIN_USERNAME \
  -e TEST_ADMIN_PASSWORD \
  web pytest tests/smoke tests/integration tests/security

echo "CSRF-enabled tests completed successfully."
