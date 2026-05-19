import math
import os
from urllib.parse import quote

PAPERLESS_API_URL = os.getenv("PAPERLESS_API_URL", "http://localhost:8000")
PAPERLESS_USERNAME = os.getenv("PAPERLESS_USERNAME", "admin")
PAPERLESS_PASSWORD = os.getenv("PAPERLESS_PASSWORD", "admin")


def _build_database_url():
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "paperless")
    user = os.getenv("DB_USER", "paperless")
    password = os.getenv("DB_PASS", "paperless-dev")
    return f"postgresql://{quote(user, safe='')}:{quote(password, safe='')}@{host}:{port}/{name}"


def _env_int(name, default, min_val=1):
    raw = os.getenv(name, default)
    try:
        value = int(raw)
    except ValueError:
        raise SystemExit(f"ERROR: {name}={raw!r} is not a valid integer")
    if value < min_val:
        raise SystemExit(f"ERROR: {name}={value} must be >= {min_val}")
    return value


def _env_float(name, default, min_val=0.0, max_val=None):
    raw = os.getenv(name, default)
    try:
        value = float(raw)
    except ValueError:
        raise SystemExit(f"ERROR: {name}={raw!r} is not a valid number")
    if not math.isfinite(value):
        raise SystemExit(f"ERROR: {name}={raw!r} must be finite")
    if value < min_val:
        raise SystemExit(f"ERROR: {name}={value} must be >= {min_val}")
    if max_val is not None and value > max_val:
        raise SystemExit(f"ERROR: {name}={value} must be <= {max_val}")
    return value


DATABASE_URL = _build_database_url()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
SYNC_INTERVAL = _env_int("SYNC_INTERVAL_SECONDS", "60")
CHUNK_SIZE = _env_int("CHUNK_SIZE_TOKENS", "500")
CHUNK_OVERLAP = _env_int("CHUNK_OVERLAP_TOKENS", "50")
MCP_PORT = _env_int("MCP_HTTP_PORT", "3001")
MCP_AUTH_TOKEN = os.getenv("MCP_AUTH_TOKEN", "")
SEMANTIC_MIN_SIMILARITY = _env_float(
    "SEMANTIC_MIN_SIMILARITY",
    "0.25",
    max_val=1.0,
)
