#!/usr/bin/env bash
set -euo pipefail

if [ -d /usr/bin ]; then
  export PATH="/usr/bin:/bin:$PATH"
fi

EXPECTED_COUNT="${EXPECTED_MEDIA_COUNT:-33827}"
MODE="${1:-uploads}"
TARGET="${2:-}"
TEMP_IMAGE="${TEMP_IMAGE:-nghcc-admin-platform-web}"

count_uploads() {
  local dir="${1:-uploads}"
  if [ ! -d "$dir" ]; then
    echo "uploads directory not found: $dir"
    exit 1
  fi
  find "$dir" -type f ! -name ".gitkeep" | wc -l | tr -d ' '
}

count_volume() {
  local volume="${1:-nghcc-admin-media-data}"
  docker volume inspect "$volume" >/dev/null 2>&1 || {
    echo "Docker volume not found: $volume"
    exit 1
  }
  docker run --rm -v "${volume}:/media:ro" "$TEMP_IMAGE" sh -c "find /media -type f ! -name .gitkeep | wc -l" | tr -d ' \r'
}

case "$MODE" in
  uploads|bind)
    TARGET="${TARGET:-uploads}"
    COUNT="$(count_uploads "$TARGET")"
    LABEL="bind mount directory $TARGET"
    ;;
  volume)
    TARGET="${TARGET:-nghcc-admin-media-data}"
    COUNT="$(count_volume "$TARGET")"
    LABEL="Docker volume $TARGET"
    ;;
  *)
    echo "Usage: $0 [uploads <path>|volume <volume-name>]"
    exit 1
    ;;
esac

echo "Media target: $LABEL"
echo "Expected files: $EXPECTED_COUNT"
echo "Current files: $COUNT"

if [ "$COUNT" -lt "$EXPECTED_COUNT" ]; then
  echo "WARNING: media count is lower than expected. Missing filename risk remains."
  exit 2
fi

if [ "$COUNT" -gt "$EXPECTED_COUNT" ]; then
  echo "WARNING: media count is higher than expected. Please check test or extra files."
  exit 3
fi

echo "Media integrity check passed."
