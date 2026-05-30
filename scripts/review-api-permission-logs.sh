#!/usr/bin/env bash
set -euo pipefail

if [ -d /usr/bin ]; then
  export PATH="/usr/bin:/bin:$PATH"
fi

COMPOSE="${COMPOSE:-docker compose}"
COMPOSE_FILES="${COMPOSE_FILES:--f docker-compose.yml -f docker-compose.volume.yml}"
SERVICE="${SERVICE:-web}"
LOG_FILE="${LOG_FILE:-}"
TAIL="${TAIL:-1000}"
ROOT_DIR="$(pwd)"
PARSER="$ROOT_DIR/scripts/api_permission_log_review.py"

if command -v cygpath >/dev/null 2>&1; then
  PARSER_MOUNT="$(cygpath -w "$PARSER")"
else
  PARSER_MOUNT="$PARSER"
fi

if [ -n "$LOG_FILE" ]; then
  if command -v cygpath >/dev/null 2>&1; then
    LOG_FILE_MOUNT="$(cygpath -w "$LOG_FILE")"
  else
    LOG_FILE_MOUNT="$LOG_FILE"
  fi

  MSYS_NO_PATHCONV=1 $COMPOSE $COMPOSE_FILES run --rm \
    -v "${PARSER_MOUNT}:/app/scripts/api_permission_log_review.py:ro" \
    -v "${LOG_FILE_MOUNT}:/app/review-api-permission.log:ro" \
    web python /app/scripts/api_permission_log_review.py /app/review-api-permission.log
  exit 0
fi

$COMPOSE $COMPOSE_FILES logs --no-color --timestamps --tail "$TAIL" "$SERVICE" | \
  MSYS_NO_PATHCONV=1 $COMPOSE $COMPOSE_FILES run --rm -T \
    -v "${PARSER_MOUNT}:/app/scripts/api_permission_log_review.py:ro" \
    web python /app/scripts/api_permission_log_review.py -
