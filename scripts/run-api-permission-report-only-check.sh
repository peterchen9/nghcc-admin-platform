#!/usr/bin/env bash
set -euo pipefail

if [ -d /usr/bin ]; then
  export PATH="/usr/bin:/bin:$PATH"
fi

COMPOSE="${COMPOSE:-docker compose}"
COMPOSE_FILES="${COMPOSE_FILES:--f docker-compose.yml -f docker-compose.volume.yml}"
REPORT_DIR="${REPORT_DIR:-reports}"
RAW_LOG="${RAW_LOG:-api-permission-report-only.log}"
CSV_FILE="${CSV_FILE:-api-permission-review.csv}"
ROOT_DIR="$(pwd)"
PARSER="$ROOT_DIR/scripts/api_permission_log_review.py"
CHECKER="$ROOT_DIR/scripts/api_permission_report_only_check.py"

mkdir -p "$REPORT_DIR"

if command -v cygpath >/dev/null 2>&1; then
  REPORT_MOUNT="$(cygpath -w "$ROOT_DIR/$REPORT_DIR")"
  PARSER_MOUNT="$(cygpath -w "$PARSER")"
  CHECKER_MOUNT="$(cygpath -w "$CHECKER")"
else
  REPORT_MOUNT="$ROOT_DIR/$REPORT_DIR"
  PARSER_MOUNT="$PARSER"
  CHECKER_MOUNT="$CHECKER"
fi

echo "Running API permission report-only local endpoint check..."
MSYS_NO_PATHCONV=1 $COMPOSE $COMPOSE_FILES run --rm -T \
  -e API_PERMISSION_MODE=report-only \
  -e REPORT_RAW_LOG="${RAW_LOG}" \
  -v "${REPORT_MOUNT}:/app/reports" \
  -v "${CHECKER_MOUNT}:/app/scripts/api_permission_report_only_check.py:ro" \
  web python /app/scripts/api_permission_report_only_check.py

echo "Exporting safe review CSV..."
MSYS_NO_PATHCONV=1 $COMPOSE $COMPOSE_FILES run --rm -T \
  -v "${REPORT_MOUNT}:/app/reports" \
  -v "${PARSER_MOUNT}:/app/scripts/api_permission_log_review.py:ro" \
  web python /app/scripts/api_permission_log_review.py "/app/reports/${RAW_LOG}" > "${REPORT_DIR}/${CSV_FILE}"

echo "Decision/reason distribution:"
MSYS_NO_PATHCONV=1 $COMPOSE $COMPOSE_FILES run --rm -T \
  -e REPORT_CSV_FILE="${CSV_FILE}" \
  -v "${REPORT_MOUNT}:/app/reports:ro" \
  web python - <<'PY'
import csv
import os
from collections import Counter

csv_path = f"/app/reports/{os.environ.get('REPORT_CSV_FILE', 'api-permission-review.csv')}"
with open(csv_path, newline="", encoding="utf-8") as handle:
    rows = list(csv.DictReader(handle))

print(f"rows={len(rows)}")
for (decision, reason), count in sorted(Counter((row["decision"], row["reason"]) for row in rows).items()):
    print(f"{decision},{reason},{count}")
PY

echo "CSV written to ${REPORT_DIR}/${CSV_FILE}"
