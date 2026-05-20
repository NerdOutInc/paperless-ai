#!/usr/bin/env bash
set -euo pipefail
cd /opt/paperless-ai

if [[ $# -lt 1 ]]; then
    echo "Usage: bash restore.sh <backup-file.sql>"
    echo ""
    echo "Available backups:"
    ls -lh backups/*.sql 2>/dev/null || echo "  (none found)"
    exit 1
fi

BACKUP_FILE="$1"
if [[ ! -f "$BACKUP_FILE" ]]; then
    echo "Error: File not found: $BACKUP_FILE"
    exit 1
fi

echo "WARNING: This will replace your current database with the backup."
read -rp "Are you sure? [y/N]: " confirm
if [[ "${confirm,,}" != "y" ]]; then
    echo "Cancelled."
    exit 0
fi

echo "Stopping Paperless and companion..."
docker compose stop paperless companion

echo "Restoring database from $BACKUP_FILE..."
docker compose exec -T db psql --single-transaction -U paperless -d paperless < "$BACKUP_FILE"

echo "Restarting services..."
docker compose up -d

echo ""
echo "[OK] Database restored. Paperless is restarting."
