# One-Click Image Builder

This directory contains all files deployed to `/opt/paperless-ai/` on DigitalOcean 1-click Marketplace droplets.

## Directory Structure

```plaintext
one-click/
├── setup/              # Interactive setup wizard (HTML + Python API)
│   ├── wizard.html     # Frontend form for configuration
│   ├── setup-api.py    # Backend API for env detection and validation
│   └── Caddyfile.setup # Caddy config for setup phase
├── templates/          # Configuration templates (rendered during setup)
│   ├── env.template    # Environment variables template
│   ├── docker-compose.yml.tpl  # Docker Compose template
│   ├── Caddyfile.ip.tpl        # Caddy template for IP-only access
│   └── Caddyfile.domain.tpl    # Caddy template for domain access
├── scripts/            # Operational scripts
│   ├── first-boot.sh   # Cloud-init entry point (runs on droplet startup)
│   ├── finalize-setup.sh # Completes setup after wizard (starts services)
│   ├── update.sh       # Pulls latest images and restarts services
│   ├── backup.sh       # Creates dated PostgreSQL database backup
│   └── restore.sh      # Restores database from backup file
└── systemd/            # Systemd service units
    ├── paperless-setup.service     # Setup wizard service
    └── paperless-setup-api.service # Setup API service
```

## Image Build Status

This directory is the droplet payload for a DigitalOcean image build. The repo
does not currently include the Packer template or snapshot-build workflow, so
there is no runnable local image-build command in this checkout.

To test payload changes on a machine, copy this directory to the path used by
the setup services:

```bash
sudo mkdir -p /opt/paperless-ai
sudo rsync -a one-click/ /opt/paperless-ai/
sudo bash -n /opt/paperless-ai/scripts/*.sh
```

A future image build should:

1. Launch an Ubuntu 24.04 droplet in NYC1
2. Install Docker, Docker Compose, and Caddy
3. Pre-pull all Docker images
4. Deploy files from `one-click/` to `/opt/paperless-ai/`
5. Install systemd services
6. Create a snapshot
7. Clean up the temporary droplet

The snapshot should be available in your DigitalOcean dashboard and replicated
to additional regions.

## Planned Automated Builds

The planned CI/CD workflow is `.github/workflows/packer-build.yml`, but that
workflow is not currently checked in. Once added, it should:

- Run weekly on Sundays at 4 AM UTC
- Run on any git tag (e.g., `v1.0.0`)
- Support manual triggering via GitHub Actions

Each build should update `docs/deploy-config.json` with the new snapshot ID,
which the deploy button reads to launch fresh droplets.

## Environment Variables

Required in `.env` after setup:

```bash
ADMIN_USER='admin'
ADMIN_PASSWORD='...'
DB_PASSWORD='...'
SECRET_KEY='...'
...
```

See `templates/env.template` for the full template with defaults.

## First Boot Flow

1. Cloud-init executes `/opt/paperless-ai/scripts/first-boot.sh`
2. Systemd services start the setup wizard (Caddy + Python stdlib API)
3. Farmer accesses `http://<droplet-ip>` to configure
4. Farmer fills out admin credentials, timezone, optional domain
5. On completion, `finalize-setup.sh` is called
6. Wizard services stop, Docker Compose services start
7. Caddy reverse-proxies Paperless on `:80`/`:443`, Search on `/search`,
   and MCP on `/mcp`

## Quick Reference

| Task | Script |
| --- | --- |
| Check setup progress | `journalctl -u paperless-setup -f` |
| View API logs | `journalctl -u paperless-setup-api -f` |
| Restart services | `cd /opt/paperless-ai && docker compose restart` |
| Backup database | `/opt/paperless-ai/scripts/backup.sh` |
| Restore database | `/opt/paperless-ai/scripts/restore.sh <backup-file>` |
| Update images | `/opt/paperless-ai/scripts/update.sh` |
