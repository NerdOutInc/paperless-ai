import hashlib
import threading
import time
import traceback
from pathlib import Path
from urllib.parse import quote

import requests
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

import config
import search


STATIC_DIR = Path(__file__).with_name("static").joinpath("search")
PAGE_DIR = Path(__file__).with_name("search_pages")
MAX_SEARCH_LIMIT = 50
MAX_QUERY_LENGTH = 500
DEFAULT_SEARCH_LIMIT = 10
SESSION_CACHE_TTL_SECONDS = 15
SESSION_CACHE_MAX_ENTRIES = 256
SESSION_VALIDATION_TIMEOUT = 3
_session_cache = {}
_session_cache_lock = threading.Lock()


def clamp_limit(raw_limit, default=DEFAULT_SEARCH_LIMIT, max_limit=MAX_SEARCH_LIMIT):
    try:
        value = int(raw_limit)
    except (TypeError, ValueError):
        return default
    return max(1, min(value, max_limit))


def cookie_header_from_request(request):
    return request.headers.get("cookie", "")


def clear_session_cache():
    with _session_cache_lock:
        _session_cache.clear()


def session_cache_key(cookie_header):
    return hashlib.sha256(cookie_header.encode("utf-8")).hexdigest()


def prune_expired_session_cache(now):
    expired_keys = [
        key
        for key, cached in _session_cache.items()
        if cached["expires_at"] <= now
    ]
    for key in expired_keys:
        _session_cache.pop(key, None)


def store_session_cache(cache_key, profile, now):
    with _session_cache_lock:
        prune_expired_session_cache(now)
        while len(_session_cache) >= SESSION_CACHE_MAX_ENTRIES:
            oldest_key = min(
                _session_cache,
                key=lambda key: _session_cache[key]["expires_at"],
            )
            _session_cache.pop(oldest_key, None)
        _session_cache[cache_key] = {
            "expires_at": now + SESSION_CACHE_TTL_SECONDS,
            "profile": profile,
        }


def login_redirect_for(request):
    target = request.url.path
    if request.url.query:
        target = f"{target}?{request.url.query}"
    return RedirectResponse(
        f"/accounts/login/?next={quote(target, safe='')}",
        status_code=302,
    )


def validate_paperless_session(cookie_header):
    if not cookie_header:
        return None

    now = time.monotonic()
    cache_key = session_cache_key(cookie_header)
    with _session_cache_lock:
        prune_expired_session_cache(now)
        cached = _session_cache.get(cache_key)
        if cached:
            return cached["profile"]

    response = requests.get(
        f"{config.PAPERLESS_API_URL}/api/profile/",
        headers={
            "Accept": "application/json",
            "Cookie": cookie_header,
        },
        timeout=SESSION_VALIDATION_TIMEOUT,
    )
    if response.status_code in (401, 403):
        store_session_cache(cache_key, None, time.monotonic())
        return None
    response.raise_for_status()

    try:
        profile = response.json()
    except ValueError:
        raise requests.RequestException("Paperless profile response was not JSON")
    if not isinstance(profile, dict):
        raise requests.RequestException("Paperless profile response was not an object")

    store_session_cache(cache_key, profile, time.monotonic())
    return profile


def api_error_response(error, status_code):
    return JSONResponse(
        {"error": error},
        status_code=status_code,
        headers={"Cache-Control": "no-store"},
    )


def log_paperless_error(context, exc):
    response = getattr(exc, "response", None)
    if response is not None:
        detail = f"status={response.status_code}"
    else:
        detail = f"type={exc.__class__.__name__}"
    print(f"{context}: Paperless API request failed ({detail})")


def search_unavailable_response():
    return HTMLResponse(
        """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Paperless-ngx Search unavailable</title>
  </head>
  <body>
    <h1>Search is temporarily unavailable</h1>
    <p>Search could not verify your Paperless session. Try again in a moment.</p>
  </body>
</html>
""",
        status_code=503,
        headers={"Cache-Control": "no-store"},
    )


def public_profile(profile):
    return {
        "id": profile.get("id"),
        "username": profile.get("username", ""),
        "email": profile.get("email", ""),
        "first_name": profile.get("first_name", ""),
        "last_name": profile.get("last_name", ""),
    }


def profile_can_view_mcp_token(profile):
    return bool(profile.get("is_superuser") or profile.get("is_staff"))


def authenticated_static_page(request, filename):
    try:
        profile = validate_paperless_session(cookie_header_from_request(request))
    except requests.RequestException as exc:
        log_paperless_error("Paperless session validation failed", exc)
        return search_unavailable_response()
    if profile is None:
        return login_redirect_for(request)

    index_path = PAGE_DIR / filename
    return HTMLResponse(
        index_path.read_text(encoding="utf-8"),
        headers={"Cache-Control": "no-store"},
    )


def search_page(request):
    return authenticated_static_page(request, "index.html")


def mcp_page(request):
    return authenticated_static_page(request, "mcp.html")


def profile_api(request):
    try:
        profile = validate_paperless_session(cookie_header_from_request(request))
    except requests.RequestException as exc:
        log_paperless_error("Paperless profile validation failed", exc)
        return api_error_response("paperless_api_error", 502)
    if profile is None:
        return api_error_response("not_authenticated", 401)
    return JSONResponse(
        {"profile": public_profile(profile)},
        headers={"Cache-Control": "no-store"},
    )


def mcp_config_api(request):
    try:
        profile = validate_paperless_session(cookie_header_from_request(request))
    except requests.RequestException as exc:
        log_paperless_error("Paperless MCP config validation failed", exc)
        return api_error_response("paperless_api_error", 502)
    if profile is None:
        return api_error_response("not_authenticated", 401)

    can_view_token = profile_can_view_mcp_token(profile)
    auth_token = config.MCP_AUTH_TOKEN if can_view_token else None
    return JSONResponse(
        {
            "server_name": "paperless-ag",
            "endpoint_path": "/mcp",
            "auth_token": auth_token,
            "can_view_token": can_view_token,
            "token_available": bool(auth_token),
            "token_configured": bool(config.MCP_AUTH_TOKEN),
        },
        headers={"Cache-Control": "no-store"},
    )


def documents_api(request):
    cookie_header = cookie_header_from_request(request)
    try:
        profile = validate_paperless_session(cookie_header)
    except requests.RequestException as exc:
        log_paperless_error("Paperless search validation failed", exc)
        return api_error_response("paperless_api_error", 502)
    if profile is None:
        return api_error_response("not_authenticated", 401)

    query = request.query_params.get("q", "").strip()
    if not query:
        return api_error_response("q is required", 400)
    if len(query) > MAX_QUERY_LENGTH:
        return api_error_response("q is too long", 400)

    limit = clamp_limit(request.query_params.get("limit"))
    try:
        results = search.hybrid_search_for_session(query, limit, cookie_header)
    except requests.HTTPError as exc:
        status_code = exc.response.status_code if exc.response is not None else 502
        if status_code in (401, 403):
            return JSONResponse(
                {"error": "not_authenticated"},
                status_code=401,
                headers={"Cache-Control": "no-store"},
            )
        log_paperless_error("Search API upstream error", exc)
        return api_error_response("paperless_api_error", 502)
    except requests.RequestException as exc:
        log_paperless_error("Search API upstream error", exc)
        return api_error_response("paperless_api_error", 502)
    except Exception as exc:
        print(f"Search API error: {exc.__class__.__name__}: {exc}")
        traceback.print_exc()
        return api_error_response("search_failed", 500)

    return JSONResponse(
        {
            "query": query,
            "limit": limit,
            "max_limit": MAX_SEARCH_LIMIT,
            "has_more_possible": (
                len(results) == limit and limit < MAX_SEARCH_LIMIT
            ),
            "count": len(results),
            "results": results,
        },
        headers={"Cache-Control": "no-store"},
    )


def routes():
    return [
        Route("/search", search_page, methods=["GET"]),
        Route("/search/", search_page, methods=["GET"]),
        Route("/search/mcp", mcp_page, methods=["GET"]),
        Route("/search/mcp/", mcp_page, methods=["GET"]),
        Route("/search/api/me", profile_api, methods=["GET"]),
        Route("/search/api/mcp-config", mcp_config_api, methods=["GET"]),
        Route("/search/api/documents", documents_api, methods=["GET"]),
        Mount(
            "/search/static",
            app=StaticFiles(directory=str(STATIC_DIR)),
            name="search-static",
        ),
    ]
