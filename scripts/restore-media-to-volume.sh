#!/usr/bin/env bash
set -euo pipefail

if [ -d /usr/bin ]; then
  export PATH="/usr/bin:/bin:$PATH"
fi

MEDIA_TAR="${1:-}"
MEDIA_VOLUME="${MEDIA_VOLUME:-nghcc-admin-media-data}"
TEMP_IMAGE="${TEMP_IMAGE:-nghcc-admin-platform-web}"
EXPECTED_COUNT="${EXPECTED_MEDIA_COUNT:-33827}"

if [ -z "$MEDIA_TAR" ]; then
  echo "Usage: $0 <nads26-media-YYYYmmdd-HHMMSS.tar.gz>"
  exit 1
fi

if [ ! -f "$MEDIA_TAR" ]; then
  echo "Media tar not found: $MEDIA_TAR"
  exit 1
fi

MEDIA_DIR="$(cd "$(dirname "$MEDIA_TAR")" && pwd)"
MEDIA_ABS="${MEDIA_DIR}/$(basename "$MEDIA_TAR")"

if command -v cygpath >/dev/null 2>&1; then
  MEDIA_TAR_WIN="$(cygpath -w "$MEDIA_ABS")"
  BACKUP_DIR_WIN="$(cygpath -w "$MEDIA_DIR")"
else
  MEDIA_TAR_WIN="$MEDIA_ABS"
  BACKUP_DIR_WIN="$MEDIA_DIR"
fi

MEDIA_BASENAME="$(basename "$MEDIA_TAR")"

echo "Ensuring Docker volume exists: $MEDIA_VOLUME"
docker volume inspect "$MEDIA_VOLUME" >/dev/null 2>&1 || docker volume create "$MEDIA_VOLUME" >/dev/null

echo "Restoring media into Docker named volume..."
echo "Source: $MEDIA_TAR_WIN"
echo "Volume: $MEDIA_VOLUME"

MSYS_NO_PATHCONV=1 docker run --rm \
  -v "${BACKUP_DIR_WIN}:/backup:ro" \
  -v "${MEDIA_VOLUME}:/media" \
  "$TEMP_IMAGE" \
  sh -c "find /media -mindepth 1 -maxdepth 1 -exec rm -rf {} + && tar -xzf '/backup/${MEDIA_BASENAME}' -C /media --strip-components=1 && find /media -type f | wc -l && du -sh /media" \
  | tee /tmp/nghcc-admin-media-restore.out

RESTORED_COUNT="$(grep -E '^[0-9]+$' /tmp/nghcc-admin-media-restore.out | tail -n 1)"

echo "Restored media files: $RESTORED_COUNT"
if [ "$RESTORED_COUNT" != "$EXPECTED_COUNT" ]; then
  echo "WARNING: expected $EXPECTED_COUNT files, got $RESTORED_COUNT."
  exit 2
fi

echo "Media restore completed and file count matches expected count."
