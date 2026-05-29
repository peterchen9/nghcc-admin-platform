#!/usr/bin/env bash
set -euo pipefail

if [ -d /usr/bin ]; then
  export PATH="/usr/bin:/bin:$PATH"
fi

BACKUP_DIR="${1:-}"

if [ -z "$BACKUP_DIR" ]; then
  echo "Usage: $0 <backup-directory>"
  exit 1
fi

if [ ! -d "$BACKUP_DIR" ]; then
  echo "Backup directory not found: $BACKUP_DIR"
  exit 1
fi

CHECKSUM_FILE="$(find "$BACKUP_DIR" -maxdepth 1 -type f -name 'SHA256SUMS-*.txt' | head -n 1)"
if [ -z "$CHECKSUM_FILE" ]; then
  echo "SHA256SUMS file not found in: $BACKUP_DIR"
  exit 1
fi

echo "Verifying checksums with: $CHECKSUM_FILE"

if command -v sha256sum >/dev/null 2>&1; then
  (
    cd "$BACKUP_DIR"
    sha256sum -c "$(basename "$CHECKSUM_FILE")"
  )
else
  echo "sha256sum is required. Use Git Bash, WSL2, or Linux."
  exit 1
fi

echo "Checksum verification completed."
