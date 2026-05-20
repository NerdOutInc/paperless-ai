import hashlib
import re
import threading
import time
import traceback
from pathlib import Path
from urllib.parse import quote, unquote

import requests
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

import config
import search


STATIC_DIR = Path(__file__).with_name("static").joinpath("search")
PAGE_DIR = Path(__file__).with_name("search_pages")
PAPERLESS_UI_SCRIPT_PATH = "/search/static/paperless-ui-link.js"
PAPERLESS_UI_SCRIPT_TAG = (
    f'<script src="{PAPERLESS_UI_SCRIPT_PATH}" defer></script>'
)
BODY_CLOSE_PATTERN = re.compile(r"</body\s*>", re.IGNORECASE)
PAPERLESS_UI_PROXY_TIMEOUT = 30
HOP_BY_HOP_HEADERS = {
    "connection",
    "content-encoding",
    "content-length",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}
PAPERLESS_UI_PROXY_DENIED_PATHS = (
    "/api",
    "/static",
    "/media",
    "/accounts",
    "/search",
    "/mcp",
    "/paperless-ui-proxy",
    "/.well-known",
)
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
    print(f"{context}: Paperless request failed ({detail})")


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


def paperless_ui_unavailable_response():
    return HTMLResponse(
        """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>Paperless-ngx unavailable</title>
  </head>
  <body>
    <h1>Paperless-ngx is temporarily unavailable</h1>
    <p>The Paperless UI could not be loaded. Try again in a moment.</p>
  </body>
</html>
""",
        status_code=503,
        headers={"Cache-Control": "no-store"},
    )


def response_headers_from_upstream(response):
    raw_headers = getattr(getattr(response, "raw", None), "headers", None)
    source = raw_headers if raw_headers is not None else response.headers
    connection_header_names = connection_header_tokens(source)
    set_cookie_values = header_values(source, "Set-Cookie")
    emitted_set_cookie = False
    headers = []
    for key, value in source.items():
        lower_key = key.lower()
        if lower_key in HOP_BY_HOP_HEADERS or lower_key in connection_header_names:
            continue
        if lower_key == "set-cookie" and set_cookie_values:
            if not emitted_set_cookie:
                headers.extend(
                    ("Set-Cookie", value) for value in set_cookie_values
                )
                emitted_set_cookie = True
            continue
        headers.append((key, value))
    if set_cookie_values and not emitted_set_cookie:
        headers.extend(("Set-Cookie", value) for value in set_cookie_values)
    return headers


def header_values(headers, key):
    for method_name in ("getlist", "get_all"):
        method = getattr(headers, method_name, None)
        if method is None:
            continue
        values = method(key)
        if values:
            return list(values)
    get = getattr(headers, "get", None)
    if get is not None:
        value = get(key)
        if value:
            return [value]
    return []


def connection_header_tokens(headers):
    tokens = set()
    for value in header_values(headers, "Connection"):
        tokens.update(
            token.strip().lower()
            for token in value.split(",")
            if token.strip()
        )
    return tokens


def response_with_upstream_headers(content, status_code, upstream_headers):
    response = Response(content, status_code=status_code)
    encoded_headers = [
        (key.lower().encode("latin-1"), value.encode("latin-1"))
        for key, value in upstream_headers
    ]
    if hasattr(response, "raw_headers"):
        response.raw_headers.extend(encoded_headers)
    else:
        for key, value in upstream_headers:
            response.headers[key] = value
    return response


def is_denied_paperless_ui_proxy_path(path):
    return any(
        path == denied_path or path.startswith(f"{denied_path}/")
        for denied_path in PAPERLESS_UI_PROXY_DENIED_PATHS
    )


def normalized_paperless_ui_proxy_path(raw_path):
    path = f"/{raw_path.lstrip('/')}" if raw_path else "/"
    decoded_path = unquote(path)
    if "\\" in decoded_path:
        return None

    segments = decoded_path.split("/")
    if any(segment == ".." for segment in segments):
        return None

    normalized_segments = [
        segment for segment in segments if segment and segment != "."
    ]
    normalized_path = f"/{'/'.join(normalized_segments)}"
    if decoded_path.endswith("/") and normalized_path != "/":
        normalized_path = f"{normalized_path}/"
    return quote(normalized_path, safe="/")


def inject_paperless_ui_script(html):
    if PAPERLESS_UI_SCRIPT_PATH in html:
        return html

    body_close_matches = list(BODY_CLOSE_PATTERN.finditer(html))
    if not body_close_matches:
        return f"{html}\n{PAPERLESS_UI_SCRIPT_TAG}\n"
    body_close_index = body_close_matches[-1].start()
    return (
        f"{html[:body_close_index]}{PAPERLESS_UI_SCRIPT_TAG}\n"
        f"{html[body_close_index:]}"
    )


def is_html_response(response):
    content_type = ""
    for key, value in response.headers.items():
        if key.lower() == "content-type":
            content_type = value
            break
    return "text/html" in content_type.lower()


def paperless_ui_proxy(request):
    proxied_path = request.path_params.get("path", "")
    upstream_path = normalized_paperless_ui_proxy_path(proxied_path)
    if upstream_path is None or is_denied_paperless_ui_proxy_path(upstream_path):
        return Response("Not found", status_code=404)

    upstream_url = f"{config.PAPERLESS_API_URL}{upstream_path}"
    if request.url.query:
        upstream_url = f"{upstream_url}?{request.url.query}"

    headers = {
        "Accept": request.headers.get("accept", "text/html"),
        "Accept-Language": request.headers.get("accept-language", ""),
        "Cookie": cookie_header_from_request(request),
        "User-Agent": request.headers.get("user-agent", ""),
    }
    headers = {key: value for key, value in headers.items() if value}

    try:
        upstream = requests.get(
            upstream_url,
            headers=headers,
            allow_redirects=False,
            timeout=PAPERLESS_UI_PROXY_TIMEOUT,
        )
    except requests.RequestException as exc:
        log_paperless_error("Paperless UI proxy failed", exc)
        return paperless_ui_unavailable_response()

    response_headers = response_headers_from_upstream(upstream)
    if upstream.status_code != 200 or not is_html_response(upstream):
        return response_with_upstream_headers(
            upstream.content,
            status_code=upstream.status_code,
            upstream_headers=response_headers,
        )

    upstream.encoding = upstream.encoding or "utf-8"
    return response_with_upstream_headers(
        inject_paperless_ui_script(upstream.text),
        status_code=upstream.status_code,
        upstream_headers=response_headers,
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
    return bool(profile.get("is_superuser"))


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
    search_limit = limit + 1 if limit < MAX_SEARCH_LIMIT else limit
    try:
        results = search.hybrid_search_for_session(
            query,
            search_limit,
            cookie_header,
        )
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

    visible_results = results[:limit]
    has_more_possible = len(results) > limit and limit < MAX_SEARCH_LIMIT

    return JSONResponse(
        {
            "query": query,
            "limit": limit,
            "max_limit": MAX_SEARCH_LIMIT,
            "has_more_possible": has_more_possible,
            "count": len(visible_results),
            "results": visible_results,
        },
        headers={"Cache-Control": "no-store"},
    )


def routes():
    return [
        Route("/paperless-ui-proxy", paperless_ui_proxy, methods=["GET"]),
        Route("/paperless-ui-proxy/", paperless_ui_proxy, methods=["GET"]),
        Route("/paperless-ui-proxy/{path:path}", paperless_ui_proxy, methods=["GET"]),
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
