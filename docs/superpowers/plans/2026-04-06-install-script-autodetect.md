# Install Script Auto-Detection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use
> superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the addon install path auto-detect credentials and match
pgvector to the existing Postgres version, so users don't have to know their
DB password or risk data loss.

**Architecture:** All changes are in `docs/install.sh`. Four functions are
modified: `detect_paperless` gains credential cascade logic,
`detect_pgvector` gains version extraction, `collect_addon_config` drops
manual prompts in favor of auto-detected values, and `do_addon_install` uses
version-matched pgvector images and runs pre-flight validation.

**Tech Stack:** Bash, Docker CLI, `docker inspect`, `psql`, `curl`

**Spec:** `docs/superpowers/specs/2026-04-06-install-script-autodetect-design.md`

---

## File Map

- Modify: `docs/install.sh`
  - `detect_paperless()` (lines 285-321) -- add credential cascade
  - `detect_pgvector()` (lines 323-344) -- add version extraction
  - `collect_addon_config()` (lines 395-454) -- replace manual prompts
  - `do_addon_install()` (lines 687-766+) -- version-matched pgvector,
    validation

No new files. No test files (this is a bash installer tested manually on
droplets per the testing matrix in the spec).

---

### Task 1: Extract Postgres Major Version in `detect_pgvector`

**Files:**

- Modify: `docs/install.sh:323-344`

The current `detect_pgvector` finds the DB container and checks if pgvector is
available, but doesn't record the Postgres major version. We need it to pick
the right pgvector image.

- [ ] **Step 1: Add version extraction to `detect_pgvector`**

Replace the `detect_pgvector` function (lines 323-344) with:

```bash
detect_pgvector() {
    # Check if the Postgres container has pgvector available
    local db_container=""

    if [[ -n "${PAPERLESS_COMPOSE_PROJECT:-}" ]]; then
        db_container=$(docker ps --filter "label=com.docker.compose.project=${PAPERLESS_COMPOSE_PROJECT}" --format "{{.ID}} {{.Image}}" 2>/dev/null | grep -i "postgres\|pgvector" | awk '{print $1}' | head -1)
    fi

    if [[ -z "$db_container" ]]; then
        return 1
    fi

    DB_CONTAINER_ID="$db_container"
    DB_IMAGE=$(docker inspect "$db_container" --format '{{.Config.Image}}' 2>/dev/null || echo "")

    # Extract Postgres major version from image tag
    # Handles: postgres:18, postgres:16.2, pgvector/pgvector:pg16, library/postgres:18-alpine
    DB_PG_MAJOR=""
    if [[ -n "$DB_IMAGE" ]]; then
        local tag="${DB_IMAGE##*:}"
        # Strip leading "pg" prefix (pgvector images use pg16, pg17, etc.)
        tag="${tag#pg}"
        # Extract leading digits as major version
        DB_PG_MAJOR=$(echo "$tag" | grep -oE '^[0-9]+')
    fi

    # Check if pgvector extension is available
    if docker exec "$db_container" psql -U "${DETECTED_DB_USER}" -d "${DETECTED_DB_NAME}" -c "SELECT 1 FROM pg_available_extensions WHERE name = 'vector'" 2>/dev/null | grep -q "1"; then
        return 0  # pgvector is available
    fi

    return 1
}
```

Key changes from the original:

- The `grep` filter now matches `pgvector` in addition to `postgres` (so it
  finds containers already using the pgvector image).
- Extracts `DB_PG_MAJOR` from the image tag. Handles `postgres:18`,
  `postgres:16.2-alpine`, `pgvector/pgvector:pg16`, etc.

- [ ] **Step 2: Verify version extraction logic manually**

Run these mental checks against the parsing logic:

| Image                             | Tag        | After strip `pg` | Major |
| --------------------------------- | ---------- | ---------------- | ----- |
| `docker.io/library/postgres:18`   | `18`       | `18`             | `18`  |
| `postgres:16.2`                   | `16.2`     | `16.2`           | `16`  |
| `postgres:16-alpine`              | `16-alpine`| `16-alpine`      | `16`  |
| `pgvector/pgvector:pg16`          | `pg16`     | `16`             | `16`  |
| `pgvector/pgvector:pg18`          | `pg18`     | `18`             | `18`  |

All produce the correct major version.

- [ ] **Step 3: Commit**

```bash
git add docs/install.sh
git commit -m "feat(install): extract Postgres major version in detect_pgvector"
```

---

### Task 2: Add Credential Cascade to `detect_paperless`

**Files:**

- Modify: `docs/install.sh:285-321`

The current function only reads credentials from the Paperless container's env
vars. We need to cascade through: Paperless container env -> Postgres
container env -> compose file -> env files.

- [ ] **Step 1: Add helper function for reading compose env files**

Add this new function immediately before `detect_paperless` (before line 285):

```bash
# Read a variable from a file (docker-compose.yml, .env, or env_file).
# Usage: read_var_from_file "VARNAME" "/path/to/file"
# Matches: VARNAME=value, VARNAME: value, VARNAME='value', VARNAME="value"
read_var_from_file() {
    local varname="$1" filepath="$2"
    [[ -f "$filepath" ]] || return 1
    local raw
    raw=$(grep -E "^\s*${varname}[=:]" "$filepath" 2>/dev/null | head -1) || return 1
    [[ -z "$raw" ]] && return 1
    # Strip key and separator (= or :), then trim whitespace and quotes
    local value
    value=$(echo "$raw" | sed -E "s/^[^=:]*[=:]\s*//" | sed -E "s/^['\"]//;s/['\"]$//")
    [[ -z "$value" ]] && return 1
    echo "$value"
}
```

- [ ] **Step 2: Expand `detect_paperless` with credential cascade**

Replace the `detect_paperless` function (lines 285-321) with:

```bash
detect_paperless() {
    # Look for running Paperless containers
    local container_id=""

    # Try by image name first
    container_id=$(docker ps --filter "ancestor=ghcr.io/paperless-ngx/paperless-ngx" --format "{{.ID}}" 2>/dev/null | head -1)

    # Fall back to name pattern
    if [[ -z "$container_id" ]]; then
        container_id=$(docker ps --format "{{.ID}} {{.Image}}" 2>/dev/null | grep -i "paperless-ngx" | awk '{print $1}' | head -1)
    fi

    if [[ -z "$container_id" ]]; then
        return 1
    fi

    PAPERLESS_CONTAINER_ID="$container_id"
    PAPERLESS_COMPOSE_DIR=$(docker inspect "$container_id" --format '{{index .Config.Labels "com.docker.compose.project.working_dir"}}' 2>/dev/null || echo "")
    PAPERLESS_COMPOSE_PROJECT=$(docker inspect "$container_id" --format '{{index .Config.Labels "com.docker.compose.project"}}' 2>/dev/null || echo "")
    PAPERLESS_SERVICE_NAME=$(docker inspect "$container_id" --format '{{index .Config.Labels "com.docker.compose.service"}}' 2>/dev/null || echo "paperless-webserver")

    # ── DB credentials cascade ──────────────────────────────
    # Source 1: Paperless container env
    local env_output
    env_output=$(docker inspect "$container_id" --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null || echo "")

    DETECTED_DB_HOST=$(echo "$env_output" | grep "^PAPERLESS_DBHOST=" | cut -d= -f2- || echo "")
    DETECTED_DB_NAME=$(echo "$env_output" | grep "^PAPERLESS_DBNAME=" | cut -d= -f2- || echo "")
    DETECTED_DB_USER=$(echo "$env_output" | grep "^PAPERLESS_DBUSER=" | cut -d= -f2- || echo "")
    DETECTED_DB_PASS=$(echo "$env_output" | grep "^PAPERLESS_DBPASS=" | cut -d= -f2- || echo "")

    # Source 2: Postgres container env (POSTGRES_PASSWORD, etc.)
    if [[ -z "$DETECTED_DB_PASS" ]] && [[ -n "${PAPERLESS_COMPOSE_PROJECT:-}" ]]; then
        local db_container
        db_container=$(docker ps --filter "label=com.docker.compose.project=${PAPERLESS_COMPOSE_PROJECT}" --format "{{.ID}} {{.Image}}" 2>/dev/null | grep -i "postgres\|pgvector" | awk '{print $1}' | head -1)
        if [[ -n "$db_container" ]]; then
            local db_env
            db_env=$(docker inspect "$db_container" --format '{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null || echo "")
            [[ -z "$DETECTED_DB_PASS" ]] && DETECTED_DB_PASS=$(echo "$db_env" | grep "^POSTGRES_PASSWORD=" | cut -d= -f2- || echo "")
            [[ -z "$DETECTED_DB_USER" ]] && DETECTED_DB_USER=$(echo "$db_env" | grep "^POSTGRES_USER=" | cut -d= -f2- || echo "")
            [[ -z "$DETECTED_DB_NAME" ]] && DETECTED_DB_NAME=$(echo "$db_env" | grep "^POSTGRES_DB=" | cut -d= -f2- || echo "")
        fi
    fi

    # Source 3: Compose file and env files on disk
    local compose_dir="${PAPERLESS_COMPOSE_DIR:-}"
    if [[ -z "$DETECTED_DB_PASS" ]] && [[ -n "$compose_dir" ]]; then
        # Try docker-compose.yml directly
        DETECTED_DB_PASS=$(read_var_from_file "PAPERLESS_DBPASS" "$compose_dir/docker-compose.yml" || echo "")
        [[ -z "$DETECTED_DB_PASS" ]] && DETECTED_DB_PASS=$(read_var_from_file "POSTGRES_PASSWORD" "$compose_dir/docker-compose.yml" || echo "")

        # Try .env file
        [[ -z "$DETECTED_DB_PASS" ]] && DETECTED_DB_PASS=$(read_var_from_file "PAPERLESS_DBPASS" "$compose_dir/.env" || echo "")
        [[ -z "$DETECTED_DB_PASS" ]] && DETECTED_DB_PASS=$(read_var_from_file "POSTGRES_PASSWORD" "$compose_dir/.env" || echo "")

        # Try env_file references (e.g., docker-compose.env)
        if [[ -z "$DETECTED_DB_PASS" ]]; then
            local env_files
            env_files=$(grep -E '^\s*-?\s*env_file:|^\s*-\s+' "$compose_dir/docker-compose.yml" 2>/dev/null | grep -oE '[a-zA-Z0-9._-]+\.env' || echo "")
            for ef in $env_files; do
                [[ -z "$DETECTED_DB_PASS" ]] && DETECTED_DB_PASS=$(read_var_from_file "PAPERLESS_DBPASS" "$compose_dir/$ef" || echo "")
                [[ -z "$DETECTED_DB_PASS" ]] && DETECTED_DB_PASS=$(read_var_from_file "POSTGRES_PASSWORD" "$compose_dir/$ef" || echo "")
            done
        fi
    fi

    # Defaults for anything not detected
    DETECTED_DB_HOST="${DETECTED_DB_HOST:-db}"
    DETECTED_DB_NAME="${DETECTED_DB_NAME:-paperless}"
    DETECTED_DB_USER="${DETECTED_DB_USER:-paperless}"

    # ── Paperless admin credentials cascade ─────────────────
    DETECTED_ADMIN_USER=$(echo "$env_output" | grep "^PAPERLESS_ADMIN_USER=" | cut -d= -f2- || echo "")
    DETECTED_ADMIN_PASS=$(echo "$env_output" | grep "^PAPERLESS_ADMIN_PASSWORD=" | cut -d= -f2- || echo "")

    if [[ -n "$compose_dir" ]]; then
        [[ -z "$DETECTED_ADMIN_USER" ]] && DETECTED_ADMIN_USER=$(read_var_from_file "PAPERLESS_ADMIN_USER" "$compose_dir/docker-compose.yml" || echo "")
        [[ -z "$DETECTED_ADMIN_PASS" ]] && DETECTED_ADMIN_PASS=$(read_var_from_file "PAPERLESS_ADMIN_PASSWORD" "$compose_dir/docker-compose.yml" || echo "")

        if [[ -z "$DETECTED_ADMIN_PASS" ]]; then
            local env_files
            env_files=$(grep -E '^\s*-?\s*env_file:|^\s*-\s+' "$compose_dir/docker-compose.yml" 2>/dev/null | grep -oE '[a-zA-Z0-9._-]+\.env' || echo "")
            for ef in $env_files; do
                [[ -z "$DETECTED_ADMIN_USER" ]] && DETECTED_ADMIN_USER=$(read_var_from_file "PAPERLESS_ADMIN_USER" "$compose_dir/$ef" || echo "")
                [[ -z "$DETECTED_ADMIN_PASS" ]] && DETECTED_ADMIN_PASS=$(read_var_from_file "PAPERLESS_ADMIN_PASSWORD" "$compose_dir/$ef" || echo "")
            done
        fi
    fi

    return 0
}
```

- [ ] **Step 3: Commit**

```bash
git add docs/install.sh
git commit -m "feat(install): cascade credential detection across multiple sources

Checks Paperless container env, Postgres container env, compose file,
and env_file references before falling back to prompting the user."
```

---

### Task 3: Add Pre-Flight Validation Functions

**Files:**

- Modify: `docs/install.sh` (add new functions after `detect_pgvector`,
  around line 344)

- [ ] **Step 1: Add validation functions**

Insert these functions after `detect_pgvector` (after line 344), before the
`# ── Collect Configuration` comment:

```bash
# ── Pre-Flight Validation ────────────────────────────────

validate_db_connection() {
    # Test that we can connect to Postgres with the detected/provided credentials
    local db_container="${DB_CONTAINER_ID:-}"
    local user="${DB_USER:-$DETECTED_DB_USER}"
    local name="${DB_NAME:-$DETECTED_DB_NAME}"
    local pass="${DB_PASS:-$DETECTED_DB_PASS}"

    if [[ -z "$db_container" ]]; then
        return 1
    fi

    if docker exec -e PGPASSWORD="$pass" "$db_container" \
        psql -U "$user" -d "$name" -c "SELECT 1" &>/dev/null; then
        return 0
    fi
    return 1
}

validate_paperless_api() {
    # Test that we can authenticate against the Paperless API
    local user="${ADMIN_USER:-}"
    local pass="${ADMIN_PASSWORD:-}"
    local paperless_url="http://localhost:8000"

    # Find the published port for the Paperless container
    if [[ -n "${PAPERLESS_CONTAINER_ID:-}" ]]; then
        local published_port
        published_port=$(docker inspect "$PAPERLESS_CONTAINER_ID" --format '{{range $p, $conf := .NetworkSettings.Ports}}{{if eq $p "8000/tcp"}}{{(index $conf 0).HostPort}}{{end}}{{end}}' 2>/dev/null || echo "")
        if [[ -n "$published_port" ]]; then
            paperless_url="http://localhost:${published_port}"
        fi
    fi

    local http_code
    http_code=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "${paperless_url}/api/token/" \
        -H "Content-Type: application/json" \
        -d "{\"username\":\"${user}\",\"password\":\"${pass}\"}" 2>/dev/null || echo "000")

    [[ "$http_code" == "200" ]]
}

validate_pgvector_image() {
    # Verify that a pgvector image exists for the detected Postgres major version
    local pg_major="${DB_PG_MAJOR:-}"
    if [[ -z "$pg_major" ]]; then
        return 1
    fi

    PGVECTOR_IMAGE="pgvector/pgvector:pg${pg_major}"

    if docker manifest inspect "$PGVECTOR_IMAGE" &>/dev/null; then
        return 0
    fi
    return 1
}
```

- [ ] **Step 2: Commit**

```bash
git add docs/install.sh
git commit -m "feat(install): add pre-flight validation for DB, API, and pgvector image"
```

---

### Task 4: Rewrite `collect_addon_config` for Auto-Detection

**Files:**

- Modify: `docs/install.sh:395-454`

Replace the manual prompting flow with auto-detection display and
prompt-only-if-missing logic.

- [ ] **Step 1: Replace `collect_addon_config`**

Replace lines 395-454 with:

```bash
collect_addon_config() {
    echo "  We found Paperless-ngx running on this server."
    echo
    info "Container: $(docker inspect "$PAPERLESS_CONTAINER_ID" --format '{{.Name}}' 2>/dev/null | sed 's/^\///')"
    [[ -n "$PAPERLESS_COMPOSE_DIR" ]] && info "Compose dir: $PAPERLESS_COMPOSE_DIR"
    info "DB host: ${DETECTED_DB_HOST}"
    info "DB name: ${DETECTED_DB_NAME}"

    # Show credential detection status
    if [[ -n "$DETECTED_DB_PASS" ]]; then
        info "DB credentials: auto-detected"
    else
        warn "DB password: not found in config"
    fi

    if [[ -n "$DETECTED_ADMIN_USER" ]] && [[ -n "$DETECTED_ADMIN_PASS" ]]; then
        info "Paperless admin: auto-detected (${DETECTED_ADMIN_USER})"
    else
        warn "Paperless admin: not found in config -- need your credentials"
    fi

    divider

    echo "  We'll add semantic search to your existing Paperless installation."
    echo "  Your existing setup will not be modified (we use a docker-compose.override.yml)."
    echo

    if ! prompt_yn "Continue?"; then
        echo "  Cancelled."
        exit 0
    fi

    # ── Use auto-detected values, prompt only for what's missing ──

    # DB credentials
    DB_HOST="$DETECTED_DB_HOST"
    DB_NAME="$DETECTED_DB_NAME"
    DB_USER="$DETECTED_DB_USER"

    if [[ -n "$DETECTED_DB_PASS" ]]; then
        DB_PASS="$DETECTED_DB_PASS"
    else
        divider
        echo "  We couldn't find the database password automatically."
        echo "  Check your docker-compose.yml for POSTGRES_PASSWORD or PAPERLESS_DBPASS."
        echo
        DB_PASS=$(prompt_secret "Postgres password")
    fi

    # Paperless admin credentials
    if [[ -n "$DETECTED_ADMIN_USER" ]] && [[ -n "$DETECTED_ADMIN_PASS" ]]; then
        ADMIN_USER="$DETECTED_ADMIN_USER"
        ADMIN_PASSWORD="$DETECTED_ADMIN_PASS"
    else
        divider
        echo "  We need your Paperless admin credentials so the companion"
        echo "  container can access the Paperless API."
        echo
        ADMIN_USER=$(prompt_safe "Paperless admin username" "${DETECTED_ADMIN_USER:-admin}")
        ADMIN_PASSWORD=$(prompt_secret "Paperless admin password")
    fi

    # ── Validate credentials ─────────────────────────────────

    divider
    step "Validating credentials..."
    echo

    # Validate DB connection (retry loop)
    while ! validate_db_connection; do
        fail "Could not connect to Postgres (user=$DB_USER, db=$DB_NAME)"
        echo "  Check POSTGRES_PASSWORD in your docker-compose.yml."
        echo
        DB_PASS=$(prompt_secret "Postgres password")
    done
    info "Database connection verified"

    # Validate Paperless API (retry loop)
    while ! validate_paperless_api; do
        fail "Could not authenticate with Paperless (user=$ADMIN_USER)"
        echo "  Check your Paperless admin username and password."
        echo
        ADMIN_USER=$(prompt_safe "Paperless admin username" "$ADMIN_USER")
        ADMIN_PASSWORD=$(prompt_secret "Paperless admin password")
    done
    info "Paperless API authentication verified"

    divider

    echo "  Do you have a domain name pointed at this server?"
    echo -e "  ${DIM}(e.g., docs.smithfarms.com)${NC}"
    echo
    DOMAIN=$(prompt_domain "Domain (or press Enter to skip)")
    if [[ -n "$DOMAIN" ]]; then
        LE_EMAIL=$(prompt_safe "Email for SSL certificate (Let's Encrypt)" "")
    fi

    MCP_AUTH_TOKEN=$(generate_password)
}
```

- [ ] **Step 2: Commit**

```bash
git add docs/install.sh
git commit -m "feat(install): auto-detect credentials, prompt only for missing values

Shows detection status upfront, validates DB and API credentials before
proceeding, and retries on failure instead of writing broken config."
```

---

### Task 5: Version-Matched pgvector in `do_addon_install`

**Files:**

- Modify: `docs/install.sh:720-756` (pgvector section of `do_addon_install`)

Replace the hardcoded `pgvector/pgvector:pg16` with version-matched image
using the `DB_PG_MAJOR` variable from Task 1 and the `validate_pgvector_image`
function from Task 3.

- [ ] **Step 1: Replace pgvector handling in `do_addon_install`**

Replace lines 720-736 (the pgvector check block inside `do_addon_install`)
with:

```bash
    # Check pgvector
    if detect_pgvector; then
        info "pgvector is available in your Postgres"
    else
        if [[ -z "${DB_PG_MAJOR:-}" ]]; then
            fail "Could not determine Postgres major version from image: ${DB_IMAGE:-unknown}"
            fail "Cannot install pgvector automatically."
            echo "  Install pgvector manually or switch to a pgvector/pgvector image."
            exit 1
        fi

        if ! validate_pgvector_image; then
            fail "No pgvector image found for Postgres ${DB_PG_MAJOR}"
            fail "pgvector/pgvector:pg${DB_PG_MAJOR} does not exist."
            echo "  Check https://hub.docker.com/r/pgvector/pgvector/tags for available versions."
            exit 1
        fi

        warn "Your Postgres doesn't have pgvector."
        if [[ -n "${DB_IMAGE:-}" ]]; then
            echo "  Current image: $DB_IMAGE"
        fi
        echo "  Replacement:   $PGVECTOR_IMAGE"
        echo
        echo "  We'll override the Postgres image to $PGVECTOR_IMAGE"
        echo "  (drop-in replacement -- your data stays intact)."
        echo
        if ! prompt_yn "Continue?"; then
            exit 0
        fi
        NEEDS_PGVECTOR_OVERRIDE=true
    fi
```

- [ ] **Step 2: Replace hardcoded pg16 in override generation**

Replace the override content line at line 755 (inside the
`NEEDS_PGVECTOR_OVERRIDE` block):

```bash
    # Old:
    #     override_content+="
    #   ${DB_HOST}:
    #     image: pgvector/pgvector:pg16"

    # New:
        override_content+="
  ${DB_HOST}:
    image: ${PGVECTOR_IMAGE}"
```

Find and replace the exact string `pgvector/pgvector:pg16` in the override
content generation with `${PGVECTOR_IMAGE}`.

- [ ] **Step 3: Commit**

```bash
git add docs/install.sh
git commit -m "fix(install): match pgvector image to existing Postgres major version

Previously hardcoded pgvector/pgvector:pg16, which destroyed databases
running newer Postgres versions. Now extracts the major version from the
running DB container and validates the pgvector image exists before
overriding."
```

---

### Task 6: End-to-End Test on Droplet

**Files:**

- No file changes. This is a manual verification task.

The droplet at 157.245.90.6 has a recovered Paperless-ngx with `postgres:18`.
Test the updated install script against it.

- [ ] **Step 1: Reset the droplet to pre-install state**

```bash
ssh root@157.245.90.6 "cd /home/paperless/paperless-ngx && \
    docker compose down && \
    rm -f docker-compose.override.yml paperless-ai.env && \
    docker compose up -d"
```

Wait for Paperless to become healthy.

- [ ] **Step 2: Copy updated install script to the droplet and run it**

```bash
scp docs/install.sh root@157.245.90.6:/tmp/install.sh
ssh root@157.245.90.6 "bash /tmp/install.sh"
```

Verify:

- Script detects `postgres:18` and proposes `pgvector/pgvector:pg18`
  (not pg16).
- DB password is auto-detected (no prompt).
- Script validates DB connection and reports success.
- If admin credentials are prompted, script validates them against the
  Paperless API before writing config.
- After install, `docker ps` shows all containers healthy.
- Companion logs show successful embedding (no "Could not connect"
  errors).

- [ ] **Step 3: Verify Paperless data intact**

```bash
ssh root@157.245.90.6 "docker exec paperless-db-1 \
    psql -U paperless -c \"SELECT count(*) FROM documents_document;\""
```

Should return the same document count as before the install.

- [ ] **Step 4: Commit any final adjustments**

If the end-to-end test reveals issues, fix them and commit.
