#!/usr/bin/env python3
"""Setup wizard API for Paperless Ag 1-click image.

Handles form submission, generates config files, and kicks off
Docker Compose via finalize-setup.sh. Runs on localhost:8080,
proxied by host Caddy.

No pip dependencies -- stdlib only.
"""

import json
import re
import secrets
import string
import subprocess
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

BASE_DIR = Path("/opt/paperless-ag")
TEMPLATES_DIR = BASE_DIR / "templates"
SETUP_STATE_FILE = BASE_DIR / ".setup-state"
SETUP_TOKEN_FILE = BASE_DIR / ".setup-token"
MAX_BODY_SIZE = 65536  # 64 KB -- plenty for the setup JSON payload

# Valid IANA timezones are in /usr/share/zoneinfo -- we check against it
ZONEINFO = Path("/usr/share/zoneinfo")

# Validation patterns -- strict allowlists prevent injection into .env
# (single-quoted), docker-compose.yml (double-quoted YAML), and Caddyfile.
_USERNAME_RE = re.compile(r'^[a-zA-Z0-9_.\-]+$')
_DOMAIN_RE = re.compile(
    r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?'
    r'(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)+$'
)
_EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$')
# Characters unsafe in single-quoted .env, double-quoted YAML, shell contexts,
# or {{KEY}} template placeholders
_UNSAFE_VALUE_RE = re.compile(r"['\"\\\n\r\x00`${}]")


def generate_secret(length=32):
    """Generate a random alphanumeric string (matches install.sh pattern)."""
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def valid_timezone(tz):
    """Check timezone exists in system zoneinfo."""
    if not tz or ".." in tz or tz.startswith("/"):
        return False
    return (ZONEINFO / tz).is_file()


def render_template(template_path, variables):
    """Replace {{KEY}} placeholders in a template file."""
    content = template_path.read_text()
    for key, value in variables.items():
        content = content.replace("{{" + key + "}}", value)
    return content


def get_state():
    """Read current setup state."""
    if SETUP_STATE_FILE.exists():
        return SETUP_STATE_FILE.read_text().strip()
    return "pending"


def set_state(state):
    """Write setup state."""
    SETUP_STATE_FILE.write_text(state)


def check_setup_token(provided):
    """Verify the provided token matches the one generated at first boot."""
    if not SETUP_TOKEN_FILE.exists():
        # Fail closed in production. Set PAPERLESS_SKIP_SETUP_TOKEN=1 for
        # local development without a token file.
        import os
        return os.environ.get("PAPERLESS_SKIP_SETUP_TOKEN") == "1"
    expected = SETUP_TOKEN_FILE.read_text().strip()
    return secrets.compare_digest(provided, expected)


class SetupHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """Suppress default access logs."""
        pass

    def _send_json(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        if self.path == "/api/status":
            self._send_json(200, {"state": get_state()})
        else:
            self._send_json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/api/setup":
            self._send_json(404, {"error": "not found"})
            return

        state = get_state()
        if state == "in_progress":
            # Allow retry if state has been stuck for over 10 minutes
            # (e.g. API crashed after setting state but before finalize ran)
            try:
                age = time.time() - SETUP_STATE_FILE.stat().st_mtime
            except OSError:
                age = 0
            if age < 600:
                self._send_json(409, {"error": "setup already in progress"})
                return
            # Stale in_progress -- fall through to allow retry
        if state == "complete":
            self._send_json(409, {"error": "setup already complete"})
            return
        # Allow retry from "pending", "failed", or stale "in_progress" state

        # Read request body
        try:
            length = int(self.headers.get("Content-Length", 0))
        except (ValueError, TypeError):
            self._send_json(400, {"error": "invalid Content-Length"})
            return
        if length > MAX_BODY_SIZE:
            self._send_json(413, {"error": "request body too large"})
            return
        body = self.rfile.read(length)
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._send_json(400, {"error": "invalid JSON"})
            return

        # Verify one-time setup token (generated at first boot)
        setup_token = data.get("setup_token", "")
        if not check_setup_token(setup_token):
            self._send_json(403, {"error": "invalid setup token"})
            return

        # Validate required fields
        admin_user = data.get("admin_user", "").strip()
        admin_password = data.get("admin_password", "").strip()
        timezone = data.get("timezone", "").strip()
        domain = data.get("domain", "").strip()
        le_email = data.get("le_email", "").strip()

        errors = []
        if not admin_user:
            errors.append("admin_user is required")
        elif not _USERNAME_RE.match(admin_user) or len(admin_user) > 150:
            errors.append("admin_user must contain only letters, digits, . _ - (max 150)")
        if not admin_password:
            errors.append("admin_password is required")
        elif len(admin_password) < 8:
            errors.append("admin_password must be at least 8 characters")
        elif _UNSAFE_VALUE_RE.search(admin_password):
            errors.append("admin_password cannot contain quotes, backslashes, backticks, $, {, }, or newlines")
        if not timezone or not valid_timezone(timezone):
            errors.append("valid timezone is required")
        if domain:
            if not _DOMAIN_RE.match(domain) or len(domain) > 253:
                errors.append("domain must be a valid hostname")
            if not le_email:
                errors.append("le_email is required when domain is provided")
            elif not _EMAIL_RE.match(le_email) or len(le_email) > 254:
                errors.append("le_email must be a valid email address")

        if errors:
            self._send_json(400, {"errors": errors})
            return

        set_state("in_progress")

        try:
            # Generate secrets
            db_password = generate_secret(32)
            secret_key = generate_secret(50)
            mcp_token = generate_secret(32)

            # Determine Paperless URL
            if domain:
                paperless_url = f"https://{domain}"
            else:
                # Get the droplet's public IP
                try:
                    ip = subprocess.check_output(
                        ["curl", "-sf", "-4", "http://169.254.169.254/metadata/v1/interfaces/public/0/ipv4/address"],
                        timeout=5,
                    ).decode().strip()
                except Exception:
                    ip = "localhost"
                paperless_url = f"http://{ip}"

            # Template variables
            variables = {
                "ADMIN_USER": admin_user,
                "ADMIN_PASSWORD": admin_password,
                "DB_PASSWORD": db_password,
                "SECRET_KEY": secret_key,
                "TIMEZONE": timezone,
                "PAPERLESS_URL": paperless_url,
                "MCP_AUTH_TOKEN": mcp_token,
                "DOMAIN": domain,
                "LE_EMAIL": le_email,
            }

            # Render config files
            env_content = render_template(
                TEMPLATES_DIR / "env.template", variables
            )

            if domain:
                caddy_content = render_template(
                    TEMPLATES_DIR / "Caddyfile.domain.tpl", variables
                )
            else:
                caddy_content = render_template(
                    TEMPLATES_DIR / "Caddyfile.ip.tpl", variables
                )

            # Write config files -- .env is the single source of truth for
            # secrets; docker-compose.yml uses ${...} references into it.
            env_path = BASE_DIR / ".env"
            env_path.write_text(env_content)
            env_path.chmod(0o600)

            compose_path = BASE_DIR / "docker-compose.yml"
            compose_path.write_text(
                (TEMPLATES_DIR / "docker-compose.yml.tpl").read_text()
            )

            (BASE_DIR / "Caddyfile").write_text(caddy_content)
        except Exception as exc:
            set_state("failed")
            log_path = BASE_DIR / "setup.log"
            log_path.write_text(f"Config generation failed: {exc}\n")
            self._send_json(500, {
                "error": "Setup failed during config generation. Check setup.log for details."
            })
            return

        # Run finalize in background so we can return the response
        # before the host Caddy shuts down.  State transitions are
        # written by finalize-setup.sh itself (this daemon thread is
        # killed by SIGTERM before it could write them).
        def finalize():
            log_path = BASE_DIR / "setup.log"
            with open(log_path, "w") as log:
                subprocess.run(
                    ["/opt/paperless-ag/scripts/finalize-setup.sh"],
                    stdout=log,
                    stderr=subprocess.STDOUT,
                )

        threading.Thread(target=finalize, daemon=True).start()

        normalized_paperless_url = paperless_url.rstrip("/")
        self._send_json(200, {
            "status": "started",
            "mcp_token": mcp_token,
            "paperless_url": paperless_url,
            "search_url": f"{normalized_paperless_url}/search",
        })


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8080), SetupHandler)
    print("Setup API listening on 127.0.0.1:8080")
    server.serve_forever()
