# DigitalOcean 1-Click Droplet Image

**Date:** 2026-04-06
**Branch:** `one-click`
**Status:** Partially implemented

## Goal

Provide non-technical users (farmers) a turnkey Paperless AI deployment
on DigitalOcean via a single link on the project website. No SSH, no
Docker knowledge, no command-line interaction required for initial setup.

## Approach

Intended image-build approach: pre-baked DigitalOcean snapshot built with
Packer. All Docker images pre-pulled. A web-based setup wizard runs on first
boot so the user configures their instance from a browser. After setup
completes, the wizard disables itself and the standard Paperless AI stack takes
over.

Current repository status: the droplet payload exists under `one-click/`, but
the `packer/` directory and `.github/workflows/packer-build.yml` workflow are
not currently checked in.

Distributed via a "Deploy on DigitalOcean" button on
`paperless.fullstack.ag` that links to the DO droplet creation page
pre-filled with the latest snapshot ID.

## Architecture

```text
User clicks deploy link
    -> DO creates droplet from snapshot
    -> cloud-init runs first-boot.sh
    -> Caddy serves setup wizard on :80
    -> User fills form (admin creds, timezone, optional domain)
    -> setup-api.py generates .env, docker-compose.yml, Caddyfile
    -> docker compose up -d
    -> Caddy swaps to production config
    -> User sees completion page with MCP token
    -> Redirects to Paperless login
```

Post-setup runtime:

```text
Caddy (:80/:443)
    /mcp/*  ->  companion:3001
    /*      ->  paperless:8000

Docker Compose:
    db          pgvector/pgvector:pg16
    redis       redis:7-alpine
    paperless   paperless-ngx:latest
    companion   ghcr.io/nerdoutinc/paperless-ai:latest
    caddy       caddy:2-alpine
```

## File Layout on Image

```text
/opt/paperless-ai/
    setup/
        wizard.html            Static HTML setup form (inline CSS/JS, no CDN deps)
        setup-api.py           Python 3 stdlib HTTP handler (~150 lines)
        Caddyfile.setup        Caddy config for wizard mode
    templates/
        docker-compose.yml     Template with ${PLACEHOLDERS}
        .env.template          Template for generated env vars
        Caddyfile.production   Caddy config template for post-setup
    scripts/
        first-boot.sh          Called by cloud-init on first boot
        finalize-setup.sh      Called by setup-api.py after form submit
        update.sh              Pull latest images + restart
        backup.sh              pg_dump wrapper
        restore.sh             psql wrapper for restoring SQL dumps
```

## Component Details

### 1. Proposed Packer Image Build

**Template:** proposed `packer/paperless-ai.pkr.hcl` (not currently checked in)

- Source: `digitalocean` builder
- Base image: Ubuntu 24.04 LTS (`ubuntu-24-04-x64`)
- Build droplet size: `s-2vcpu-4gb`
- Region: `nyc1` (snapshots available in all regions)
- Snapshot name: `paperless-ai-{{timestamp}}`

**Provision script**: proposed `packer/provision.sh` (not currently checked in):

1. `apt update && apt upgrade` for latest security patches
2. Install Docker CE + Docker Compose v2 from official Docker apt repo
3. Install Caddy on the host (for the setup wizard -- separate from the
   Docker Caddy that runs in production). Installed via official Caddy apt repo.
4. Verify Python 3 is present (ships with Ubuntu 24.04)
5. `docker compose pull` all images via a build-time compose file
6. Copy `/opt/paperless-ai/` file tree into place
7. Install + enable `paperless-setup.service` (systemd, runs host Caddy +
   setup-api.py -- NOT the Docker Caddy)
8. Snapshot hygiene:
   - Clear apt cache
   - Truncate system logs
   - Remove SSH host keys (regenerated on first boot)
   - Clear bash history
   - Clear cloud-init state so it re-runs on first real boot

### 2. First Boot (Cloud-Init)

`first-boot.sh` runs via cloud-init on the user's new droplet:

1. Regenerate SSH host keys
2. Start `paperless-setup.service` systemd unit
3. Caddy begins serving the setup wizard on port 80

No Docker containers start until the user completes the wizard.

### 3. Setup Wizard

**`wizard.html`** -- Single static HTML page, no build step:

- Inline CSS and JS (no external CDN dependencies)
- Form fields:
  - Admin username (required)
  - Admin password + confirmation (required)
  - Timezone dropdown (default: America/Chicago)
  - Domain name (optional, text input -- "leave blank to use IP address")
  - Email for Let's Encrypt (shown conditionally when domain is provided)
- Client-side validation: passwords match, required fields filled, domain
  format check
- Three UI states:
  1. Form (initial)
  2. Progress spinner ("Setting up your system...")
  3. Completion page

**Completion page shows:**

- "Paperless AI is ready!" heading
- Link to the Paperless UI (domain or IP)
- MCP auth token in a read-only field with a "Copy" button
- "Save this token -- you'll need it to connect Claude"
- "Lost your token? SSH in and run:
  `cat /opt/paperless-ai/.env | grep MCP_AUTH_TOKEN`"
- Auto-redirects to Paperless login after 30 seconds

**`setup-api.py`** -- Python 3 stdlib HTTP handler:

- No pip dependencies, no virtualenv -- runs on system Python
- Endpoints:
  - `POST /api/setup` -- validate inputs, generate configs, start stack,
    return JSON with MCP token
  - `GET /api/status` -- returns setup state (pending/in_progress/complete)
    for frontend polling
- Runs on localhost:8080, Caddy proxies `/api/*` to it

**`Caddyfile.setup`:**

```caddyfile
:80 {
    @api path /api/*
    handle @api {
        reverse_proxy localhost:8080
    }
    handle {
        file_server {
            root /opt/paperless-ai/setup
            index wizard.html
        }
    }
}
```

**Processing logic** (in `setup-api.py` / `finalize-setup.sh`):

1. Validate inputs (non-empty user/pass, valid timezone, domain format if
   provided)
2. Generate secrets:
   - DB password: random 32 chars `[A-Za-z0-9]`
   - Django secret key: random 50+ chars
   - MCP auth token: random 32 chars
3. Render `.env` from template with all values
4. Render `docker-compose.yml` from template
5. Generate production Caddyfile (domain or IP mode)
6. Start the setup/finalization process and return immediately with JSON
   response: `{"status": "started", "mcp_token": "...", "paperless_url": "..."}`
7. Client polls `/api/status` to determine when setup has completed or
   failed
8. In the background, run `docker compose up -d`
9. Wait for Paperless healthcheck to pass
10. Register daily backup cron (7 AM)
11. Stop `paperless-setup.service` (which runs the host Caddy +
    setup-api.py) after setup completes successfully. The production Caddy
    runs as a Docker container inside Docker Compose, so no config swap is
    needed -- `docker compose up -d` already starts it. The systemd service
    simply stops to free port 80.

### 4. Post-Setup Runtime

Identical to the existing Paperless AI production stack:

- All services managed by Docker Compose
- Caddy reverse-proxies Paperless and MCP
- HTTPS via Let's Encrypt if domain was provided
- Daily backup cron at 7 AM

**Helper scripts:**

- `update.sh`: backs up DB, pulls latest images, restarts stack
- `backup.sh`: `pg_dump` wrapper, writes to `/opt/paperless-ai/backups/`
- `restore.sh`: `psql` wrapper for restoring SQL dumps

**Re-running setup:** Not supported via the web wizard. If reconfiguration
is needed, the user SSHes in and edits `/opt/paperless-ai/.env` + restarts
Docker Compose. This is intentional -- re-running setup on a system with
existing data is risky.

### 5. Proposed CI Pipeline

**Workflow:** proposed `.github/workflows/packer-build.yml` (not currently
checked in)

- Triggers:
  - Weekly schedule (Sunday night)
  - Manual dispatch
  - On release tags
- Repo secret required: `DIGITALOCEAN_API_TOKEN`
- Steps:
  1. Checkout repository
  2. Install Packer
  3. `packer init`
  4. `packer build` -- creates new snapshot
  5. Write snapshot ID to `docs/deploy-config.json`
  6. Commit and push `deploy-config.json` to the repo
  7. Delete previous snapshot via DO API (avoid accumulating costs)

**`docs/deploy-config.json`:**

```json
{
  "snapshot_id": "123456789",
  "built_at": "2026-04-06T00:00:00Z",
  "droplet_size": "s-2vcpu-4gb"
}
```

### 6. Distribution

**Deploy link format:**

```text
https://cloud.digitalocean.com/droplets/new?image=SNAPSHOT_ID&size=s-2vcpu-4gb
```

**Website integration:** The landing page at `paperless.fullstack.ag`
fetches `deploy-config.json` client-side and constructs the deploy link
dynamically. A "Deploy on DigitalOcean" button (with DO logo) links to
the constructed URL.

**Landing page content:**

- What they'll get (Paperless AI -- document management for farms)
- Cost: ~$24/mo on DigitalOcean
- Requirement: DigitalOcean account
- Steps: click button, create droplet, visit IP, fill setup wizard

**Snapshot sharing limitation:** The snapshot lives in the project's DO
account. Users create droplets from it via the shared link. If the
snapshot is deleted, existing droplets keep running but no new ones can be
created. The weekly CI rebuild + old snapshot deletion means there's
always exactly one current snapshot.

## Recommended Droplet Size

`s-2vcpu-4gb` ($24/mo). The embedding model, Paperless, and Postgres all
benefit from 4GB RAM. The existing install script validates 1.9GB minimum
/ 3.9GB recommended, so this is the right fit.

## Out of Scope

- **App Platform deployment** -- deferred, can add later as a separate path
- **DO Marketplace listing** -- can submit the same Packer image later if
  desired
- **Web-based reconfiguration** -- post-setup changes are SSH + edit `.env`
- **Multi-region replication** -- DO handles snapshot availability across
  regions automatically
- **Setup wizard re-run** -- intentionally disabled after first setup

## Relationship to Existing Install Script

The existing `docs/install.sh` handles both fresh and add-on installs on
any Linux server. The 1-click image is a parallel deployment path, not a
replacement. The install script remains for users who want to deploy on
their own infrastructure or add to an existing Paperless instance.

The Packer provisioning reuses concepts from the install script (same
Docker Compose structure, same env vars, same helper scripts) but is
purpose-built for the snapshot workflow rather than calling the install
script directly. This avoids the interactive prompts and detection logic
that the install script needs but the pre-baked image does not.
