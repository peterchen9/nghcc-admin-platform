#!/usr/bin/env bash
set -euo pipefail

if [ -d /usr/bin ]; then
  export PATH="/usr/bin:/bin:$PATH"
fi

SQL_GZ="${1:-}"
EXPECTED_TABLES="${EXPECTED_TABLES:-52}"
COMPOSE="${COMPOSE:-docker compose}"
DB_CONTAINER="${DB_CONTAINER:-nghcc-admin-db}"

if [ -z "$SQL_GZ" ]; then
  echo "Usage: $0 <nads26db-YYYYmmdd-HHMMSS.sql.gz>"
  exit 1
fi

if [ ! -f "$SQL_GZ" ]; then
  echo "SQL dump not found: $SQL_GZ"
  exit 1
fi

if [ ! -f ".env" ]; then
  echo ".env does not exist."
  exit 1
fi

read_env() {
  local key="$1"
  local default_value="$2"
  local value
  value="$(grep -E "^${key}=" .env | tail -n 1 | sed "s/^${key}=//" | sed 's/^"//' | sed 's/"$//' | sed "s/^'//" | sed "s/'$//")"
  if [ -z "$value" ]; then
    printf "%s" "$default_value"
  else
    printf "%s" "$value"
  fi
}

DB_NAME="$(read_env DB_NAME nghcc_admin)"
DB_USER="$(read_env DB_USER nghcc_admin)"
DB_PASSWORD="$(read_env DB_PASSWORD change_me_password)"

echo "This will replace local database '$DB_NAME' in container '$DB_CONTAINER'."
echo "Source dump: $SQL_GZ"
if [ "${YES:-}" != "1" ]; then
  printf "Type RESTORE to continue: "
  read -r CONFIRM
  if [ "$CONFIRM" != "RESTORE" ]; then
    echo "Restore cancelled."
    exit 1
  fi
fi

echo "Ensuring database exists..."
$COMPOSE exec -T db sh -c "mysql -u\"\$MYSQL_USER\" -p\"\$MYSQL_PASSWORD\" -e 'DROP DATABASE IF EXISTS \`$DB_NAME\`; CREATE DATABASE \`$DB_NAME\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;'"

echo "Importing SQL dump..."
gzip -dc "$SQL_GZ" | docker exec -i "$DB_CONTAINER" sh -c "mysql -u\"$DB_USER\" -p\"$DB_PASSWORD\" \"$DB_NAME\""

TABLE_COUNT="$($COMPOSE exec -T db sh -c "mysql -u\"\$MYSQL_USER\" -p\"\$MYSQL_PASSWORD\" -N -e \"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='$DB_NAME';\" \"$DB_NAME\"" | tr -d '\r')"
echo "Database tables: $TABLE_COUNT"

if [ "$TABLE_COUNT" != "$EXPECTED_TABLES" ]; then
  echo "WARNING: expected $EXPECTED_TABLES tables, got $TABLE_COUNT."
  exit 2
fi

echo "Database restore completed and table count matches expected count."
