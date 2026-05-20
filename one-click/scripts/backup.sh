#!/usr/bin/env bash
set -euo pipefail
umask 077
cd /opt/paperless-ai

BACKUP_DIR="backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="$BACKUP_DIR/paperless-$TIMESTAMP.sql"

mkdir -p "$BACKUP_DIR"
echo "Backing up database..."
docker compose exec -T db pg_dump --clean -U paperless paperless > "$BACKUP_FILE"
echo "[OK] Backup saved to $BACKUP_FILE"

# Keep only the last 7 daily backups
ls -t "$BACKUP_DIR"/paperless-*.sql 2>/dev/null | tail -n +8 | xargs -r rm
echo "[OK] Old backups cleaned up (keeping last 7)"
