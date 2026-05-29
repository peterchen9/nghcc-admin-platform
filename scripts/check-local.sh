#!/usr/bin/env sh
set -eu

WEB_URL="${WEB_URL:-http://localhost:26001/}"
HEALTH_URL="${HEALTH_URL:-http://localhost:26001/api/health/}"
COMPOSE="${COMPOSE:-docker compose}"

echo "Checking local files..."
test -f .env || {
  echo ".env does not exist."
  exit 1
}

test -d uploads || {
  echo "uploads directory does not exist."
  exit 1
}

echo "Checking Docker Compose containers..."
$COMPOSE ps

WEB_STATUS="$($COMPOSE ps web --status running 2>/dev/null | grep -c "nghcc-admin-web" || true)"
if [ "$WEB_STATUS" -lt 1 ]; then
  echo "web container is not running."
  exit 1
fi

DB_HEALTH="$($COMPOSE ps db 2>/dev/null | grep -c "healthy" || true)"
if [ "$DB_HEALTH" -lt 1 ]; then
  echo "db container is not healthy."
  exit 1
fi

echo "Checking health endpoint..."
if command -v curl >/dev/null 2>&1; then
  HEALTH_BODY="$(curl -fsS "$HEALTH_URL")"
else
  echo "curl is required for HTTP checks."
  exit 1
fi

echo "$HEALTH_BODY" | grep -q '"database"[[:space:]]*:[[:space:]]*"ok"' || {
  echo "health endpoint did not report database ok."
  exit 1
}

echo "Checking web page..."
curl -fsS "$WEB_URL" | grep -q "sidebar" || {
  echo "web content check failed: sidebar marker was not found."
  exit 1
}

echo "Local health check completed."
