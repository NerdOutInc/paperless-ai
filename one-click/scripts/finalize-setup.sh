#!/usr/bin/env bash
set -euo pipefail
cd /opt/paperless-ai

echo "Starting Paperless AI stack..."

# Stop only the host Caddy so port 80 is free for the Docker Caddy.
# Do NOT stop paperless-setup-api.service here -- this script runs as a
# child of that service, so stopping it would kill this process mid-setup.
systemctl stop paperless-setup.service

docker compose up -d

echo "Waiting for Paperless to become healthy..."
timeout=300
elapsed=0
while [[ $elapsed -lt $timeout ]]; do
    if docker compose ps paperless 2>/dev/null | grep -q "(healthy)"; then
        echo "[OK] Paperless is healthy"
        break
    fi
    sleep 5
    elapsed=$((elapsed + 5))
done

if [[ $elapsed -ge $timeout ]]; then
    echo "[!] Paperless did not become healthy within ${timeout}s"
    echo "failed" > /opt/paperless-ai/.setup-state
    exit 1
fi

# Write state before stopping the API -- the Python daemon thread is killed
# by SIGTERM before it can write this itself (KillMode=process).
echo "complete" > /opt/paperless-ai/.setup-state

# Now that the stack is up, disable and stop both setup services
systemctl disable --now paperless-setup.service paperless-setup-api.service

# Remove setup-only artifacts so the bootstrap token is no longer exposed
rm -f /etc/update-motd.d/99-paperless-setup
if command -v shred >/dev/null 2>&1; then
    shred -u /opt/paperless-ai/.setup-token 2>/dev/null || true
else
    rm -f /opt/paperless-ai/.setup-token
fi

# Register daily backup cron at 7 AM (idempotent)
cron_line="0 7 * * * /opt/paperless-ai/scripts/backup.sh >> /opt/paperless-ai/backups/cron.log 2>&1"
if command -v crontab >/dev/null 2>&1; then
    existing_crontab="$(crontab -l 2>/dev/null || true)"
    if ! printf '%s\n' "$existing_crontab" | grep -Fqx "$cron_line"; then
        printf '%s\n%s\n' "$existing_crontab" "$cron_line" | crontab -
    fi
else
    echo "[WARN] crontab not found; skipping daily backup cron"
fi

echo "[OK] Setup complete"
