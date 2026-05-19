# One-Click Image Builder

This directory contains all files deployed to `/opt/paperless-ag/` on DigitalOcean 1-click Marketplace droplets.

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

## Building Locally

Prerequisites:

- [Packer](https://www.packer.io/downloads) (v1.8+)
- DigitalOcean account with API token

Build the snapshot:

```bash
cd packer
packer init .
DIGITALOCEAN_API_TOKEN=<your-token> packer build paperless-ag.pkr.hcl
```

The build process:

1. Launches an Ubuntu 24.04 droplet in NYC1
2. Installs Docker, Docker Compose, and Caddy
3. Pre-pulls all Docker images
4. Deploys files from `one-click/` to `/opt/paperless-ag/`
5. Installs systemd services
6. Creates a snapshot
7. Cleans up the temporary droplet

Snapshot will be available in your DigitalOcean dashboard and replicated to additional regions.

## Automated Builds

The CI/CD workflow at `.github/workflows/packer-build.yml`:

- Runs weekly on Sundays at 4 AM UTC
- Runs on any git tag (e.g., `v1.0.0`)
- Can be triggered manually via GitHub Actions

Each build updates `docs/deploy-config.json` with the new snapshot ID, which the deploy button reads to launch fresh droplets.

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

1. Cloud-init executes `/opt/paperless-ag/scripts/first-boot.sh`
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
| Restart services | `cd /opt/paperless-ag && docker compose restart` |
| Backup database | `/opt/paperless-ag/scripts/backup.sh` |
| Restore database | `/opt/paperless-ag/scripts/restore.sh <backup-file>` |
| Update images | `/opt/paperless-ag/scripts/update.sh` |
