import importlib.util
import json
import os
import sys
import time
import types
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import requests


def install_missing_dependency_stubs():
    if importlib.util.find_spec("sentence_transformers") is None:
        sentence_transformers = types.ModuleType("sentence_transformers")

        class StubEmbedding(list):
            def tolist(self):
                return list(self)

        class SentenceTransformer:
            def __init__(self, *_args, **_kwargs):
                pass

            def encode(self, value):
                if isinstance(value, list):
                    return StubEmbedding([[0.0] for _item in value])
                return StubEmbedding([0.0])

        sentence_transformers.SentenceTransformer = SentenceTransformer
        sys.modules["sentence_transformers"] = sentence_transformers

    if importlib.util.find_spec("psycopg2") is None:
        psycopg2 = types.ModuleType("psycopg2")
        psycopg2.connect = lambda *_args, **_kwargs: None
        sys.modules["psycopg2"] = psycopg2

    if importlib.util.find_spec("pgvector") is None:
        pgvector = types.ModuleType("pgvector")
        pgvector.__path__ = []
        pgvector_psycopg2 = types.ModuleType("pgvector.psycopg2")
        pgvector_psycopg2.register_vector = lambda *_args, **_kwargs: None
        pgvector.psycopg2 = pgvector_psycopg2
        sys.modules["pgvector"] = pgvector
        sys.modules["pgvector.psycopg2"] = pgvector_psycopg2

    if importlib.util.find_spec("starlette") is None:
        starlette = types.ModuleType("starlette")
        starlette.__path__ = []
        starlette_responses = types.ModuleType("starlette.responses")
        starlette_routing = types.ModuleType("starlette.routing")
        starlette_staticfiles = types.ModuleType("starlette.staticfiles")

        class Response:
            def __init__(self, content="", status_code=200, headers=None):
                self.status_code = status_code
                self.headers = headers or {}
                self.body = str(content).encode("utf-8")

        class HTMLResponse(Response):
            pass

        class JSONResponse(Response):
            def __init__(self, content, status_code=200, headers=None):
                super().__init__(json.dumps(content), status_code, headers)

        class RedirectResponse(Response):
            def __init__(self, url, status_code=302, headers=None):
                response_headers = dict(headers or {})
                response_headers["location"] = url
                super().__init__("", status_code, response_headers)

        class Route:
            def __init__(self, *_args, **_kwargs):
                pass

        class Mount(Route):
            pass

        class StaticFiles:
            def __init__(self, *_args, **_kwargs):
                pass

        starlette_responses.HTMLResponse = HTMLResponse
        starlette_responses.JSONResponse = JSONResponse
        starlette_responses.RedirectResponse = RedirectResponse
        starlette_responses.Response = Response
        starlette_routing.Mount = Mount
        starlette_routing.Route = Route
        starlette_staticfiles.StaticFiles = StaticFiles
        starlette.responses = starlette_responses
        starlette.routing = starlette_routing
        starlette.staticfiles = starlette_staticfiles
        sys.modules["starlette"] = starlette
        sys.modules["starlette.responses"] = starlette_responses
        sys.modules["starlette.routing"] = starlette_routing
        sys.modules["starlette.staticfiles"] = starlette_staticfiles


install_missing_dependency_stubs()

APP_DIR = Path(
    os.environ.get(
        "PAPERLESS_AI_APP_DIR",
        Path(__file__).resolve().parents[1] / "app",
    )
)
sys.path.insert(0, str(APP_DIR))

import config  # noqa: E402
import search  # noqa: E402
import web_search  # noqa: E402


class FakeResponse:
    def __init__(
        self,
        status_code=200,
        payload=None,
        json_error=False,
        text=None,
        headers=None,
        content=None,
        raw_headers=None,
    ):
        self.status_code = status_code
        self._payload = payload or {}
        self._json_error = json_error
        self.headers = headers or {}
        self.text = text if text is not None else json.dumps(self._payload)
        self.content = content if content is not None else self.text.encode("utf-8")
        self.encoding = "utf-8"
        if raw_headers is not None:
            self.raw = SimpleNamespace(headers=FakeRawHeaders(raw_headers))

    def json(self):
        if self._json_error:
            raise ValueError("not json")
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests

            error = requests.HTTPError(f"HTTP {self.status_code}")
            error.response = self
            raise error


class FakeRawHeaders:
    def __init__(self, headers):
        self._headers = headers

    def items(self):
        return list(self._headers)


class WebSearchTests(unittest.TestCase):
    def setUp(self):
        web_search.clear_session_cache()

    def test_clamp_limit_handles_bad_and_out_of_range_values(self):
        self.assertEqual(web_search.clamp_limit(None), 10)
        self.assertEqual(web_search.clamp_limit("nope"), 10)
        self.assertEqual(web_search.clamp_limit("0"), 1)
        self.assertEqual(web_search.clamp_limit("500"), 50)
        self.assertEqual(web_search.clamp_limit("12"), 12)

    @patch("web_search.validate_paperless_session", return_value={"username": "admin"})
    @patch(
        "web_search.search.hybrid_search_for_session",
        return_value=[{"id": 1}, {"id": 2}],
    )
    def test_documents_api_probes_for_more_results(self, hybrid_search, _validate):
        request = SimpleNamespace(
            headers={"cookie": "sessionid=abc"},
            query_params={"q": "crop", "limit": "1"},
        )

        response = web_search.documents_api(request)
        payload = json.loads(response.body)

        self.assertEqual(payload["count"], 1)
        self.assertEqual(payload["limit"], 1)
        self.assertEqual(payload["max_limit"], web_search.MAX_SEARCH_LIMIT)
        self.assertTrue(payload["has_more_possible"])
        self.assertEqual(payload["results"], [{"id": 1}])
        hybrid_search.assert_called_once_with("crop", 2, "sessionid=abc")

    @patch("web_search.validate_paperless_session", return_value={"username": "admin"})
    @patch(
        "web_search.search.hybrid_search_for_session",
        return_value=[{"id": index} for index in range(web_search.MAX_SEARCH_LIMIT)],
    )
    def test_documents_api_does_not_probe_beyond_max_limit(self, hybrid_search, _validate):
        request = SimpleNamespace(
            headers={"cookie": "sessionid=abc"},
            query_params={"q": "crop", "limit": str(web_search.MAX_SEARCH_LIMIT)},
        )

        response = web_search.documents_api(request)
        payload = json.loads(response.body)

        self.assertEqual(payload["count"], web_search.MAX_SEARCH_LIMIT)
        self.assertFalse(payload["has_more_possible"])
        hybrid_search.assert_called_once_with(
            "crop",
            web_search.MAX_SEARCH_LIMIT,
            "sessionid=abc",
        )

    @patch("web_search.validate_paperless_session", return_value={"username": "admin"})
    def test_documents_api_rejects_empty_query(self, _validate):
        request = SimpleNamespace(
            headers={"cookie": "sessionid=abc"},
            query_params={"q": "   "},
        )

        response = web_search.documents_api(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.body), {"error": "q is required"})

    @patch("web_search.validate_paperless_session", return_value={"username": "admin"})
    @patch("web_search.search.hybrid_search_for_session")
    def test_documents_api_rejects_oversized_query(self, hybrid_search, _validate):
        request = SimpleNamespace(
            headers={"cookie": "sessionid=abc"},
            query_params={"q": "x" * (web_search.MAX_QUERY_LENGTH + 1)},
        )

        response = web_search.documents_api(request)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(json.loads(response.body), {"error": "q is too long"})
        hybrid_search.assert_not_called()

    @patch("web_search.requests.get")
    def test_validate_session_returns_none_for_unauthenticated_cookie(self, get):
        get.return_value = FakeResponse(403, {"detail": "not authenticated"})

        self.assertIsNone(web_search.validate_paperless_session("sessionid=bad"))

    @patch("web_search.requests.get")
    def test_validate_session_caches_profile_briefly(self, get):
        get.return_value = FakeResponse(200, {"username": "admin"})

        first = web_search.validate_paperless_session("sessionid=abc")
        second = web_search.validate_paperless_session("sessionid=abc")

        self.assertEqual(first, {"username": "admin"})
        self.assertEqual(second, {"username": "admin"})
        get.assert_called_once()
        self.assertEqual(
            get.call_args.kwargs["timeout"],
            web_search.SESSION_VALIDATION_TIMEOUT,
        )

    @patch("web_search.requests.get")
    def test_validate_session_prunes_expired_cache_entries(self, get):
        with web_search._session_cache_lock:
            web_search._session_cache["expired"] = {
                "expires_at": time.monotonic() - 1,
                "profile": {"username": "old"},
            }
        get.return_value = FakeResponse(200, {"username": "admin"})

        web_search.validate_paperless_session("sessionid=abc")

        self.assertNotIn("expired", web_search._session_cache)

    @patch("web_search.requests.get")
    def test_validate_session_limits_cache_size(self, get):
        now = time.monotonic()
        with web_search._session_cache_lock:
            for index in range(web_search.SESSION_CACHE_MAX_ENTRIES):
                web_search._session_cache[f"cached-{index}"] = {
                    "expires_at": now + index + 1,
                    "profile": {"username": str(index)},
                }
        get.return_value = FakeResponse(200, {"username": "admin"})

        web_search.validate_paperless_session("sessionid=abc")

        self.assertLessEqual(
            len(web_search._session_cache),
            web_search.SESSION_CACHE_MAX_ENTRIES,
        )

    @patch("web_search.requests.get")
    def test_validate_session_rejects_non_json_profile_response(self, get):
        get.return_value = FakeResponse(200, json_error=True)

        with self.assertRaises(requests.RequestException):
            web_search.validate_paperless_session("sessionid=abc")

        self.assertEqual(web_search._session_cache, {})

    def test_login_redirect_fully_encodes_next_url(self):
        request = SimpleNamespace(
            url=SimpleNamespace(path="/search", query="q=a&foo=b"),
        )

        response = web_search.login_redirect_for(request)

        self.assertEqual(
            response.headers["location"],
            "/accounts/login/?next=%2Fsearch%3Fq%3Da%26foo%3Db",
        )

    @patch("web_search.validate_paperless_session", side_effect=requests.Timeout("slow"))
    def test_profile_api_returns_controlled_error_when_paperless_is_unavailable(
        self,
        _validate,
    ):
        request = SimpleNamespace(headers={"cookie": "sessionid=abc"})

        response = web_search.profile_api(request)

        self.assertEqual(response.status_code, 502)
        self.assertEqual(json.loads(response.body), {"error": "paperless_api_error"})

    @patch("web_search.validate_paperless_session", return_value=None)
    def test_mcp_config_api_requires_session(self, _validate):
        request = SimpleNamespace(headers={"cookie": ""})

        response = web_search.mcp_config_api(request)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(json.loads(response.body), {"error": "not_authenticated"})

    def test_authenticated_html_is_not_in_public_static_directory(self):
        self.assertFalse((web_search.STATIC_DIR / "index.html").exists())
        self.assertFalse((web_search.STATIC_DIR / "mcp.html").exists())

    def test_inject_paperless_ui_script_inserts_before_body_close(self):
        html = "<html><body><pngx-root></pngx-root></body></html>"

        injected = web_search.inject_paperless_ui_script(html)

        self.assertIn(web_search.PAPERLESS_UI_SCRIPT_TAG, injected)
        self.assertLess(
            injected.index(web_search.PAPERLESS_UI_SCRIPT_TAG),
            injected.lower().index("</body>"),
        )

    def test_inject_paperless_ui_script_is_idempotent(self):
        html = (
            "<html><body>"
            f"{web_search.PAPERLESS_UI_SCRIPT_TAG}"
            "</body></html>"
        )

        injected = web_search.inject_paperless_ui_script(html)

        self.assertEqual(injected.count(web_search.PAPERLESS_UI_SCRIPT_PATH), 1)

    def test_inject_paperless_ui_script_handles_missing_body_close(self):
        html = "<html><body><pngx-root></pngx-root>"

        injected = web_search.inject_paperless_ui_script(html)

        self.assertTrue(injected.endswith(f"{web_search.PAPERLESS_UI_SCRIPT_TAG}\n"))

    def test_inject_paperless_ui_script_uses_original_html_indices(self):
        html = "<html><body>Turkish dotted İ</BoDy></html>"

        injected = web_search.inject_paperless_ui_script(html)

        self.assertIn("Turkish dotted İ", injected)
        self.assertIn(f"{web_search.PAPERLESS_UI_SCRIPT_TAG}\n</BoDy>", injected)

    def test_response_headers_from_upstream_removes_recomputed_headers(self):
        response = FakeResponse(
            headers={
                "Content-Type": "text/html; charset=utf-8",
                "Content-Length": "123",
                "Content-Encoding": "gzip",
                "Location": "/dashboard",
            },
        )

        headers = web_search.response_headers_from_upstream(response)

        self.assertIn(("Content-Type", "text/html; charset=utf-8"), headers)
        self.assertIn(("Location", "/dashboard"), headers)
        self.assertNotIn(("Content-Length", "123"), headers)
        self.assertNotIn(("Content-Encoding", "gzip"), headers)

    def test_response_headers_from_upstream_removes_connection_tokens(self):
        response = FakeResponse(
            headers={
                "Connection": "X-Upstream-Hop, keep-alive",
                "Content-Type": "text/html; charset=utf-8",
                "Location": "/dashboard",
                "X-Upstream-Hop": "drop-me",
            },
        )

        headers = web_search.response_headers_from_upstream(response)

        self.assertIn(("Content-Type", "text/html; charset=utf-8"), headers)
        self.assertIn(("Location", "/dashboard"), headers)
        self.assertNotIn(("Connection", "X-Upstream-Hop, keep-alive"), headers)
        self.assertNotIn(("X-Upstream-Hop", "drop-me"), headers)

    def test_response_headers_from_upstream_preserves_duplicate_raw_headers(self):
        response = FakeResponse(
            headers={"Set-Cookie": "sessionid=abc, csrftoken=def"},
            raw_headers=[
                ("Set-Cookie", "sessionid=abc; Path=/"),
                ("Set-Cookie", "csrftoken=def; Path=/"),
                ("Content-Length", "123"),
            ],
        )

        headers = web_search.response_headers_from_upstream(response)

        self.assertEqual(
            [
                ("Set-Cookie", "sessionid=abc; Path=/"),
                ("Set-Cookie", "csrftoken=def; Path=/"),
            ],
            headers,
        )

    def test_response_headers_from_upstream_uses_raw_set_cookie_list(self):
        class CombinedCookieHeaders:
            def items(self):
                return [
                    ("Set-Cookie", "sessionid=abc, csrftoken=def"),
                    ("Content-Type", "text/html"),
                ]

            def getlist(self, key):
                if key.lower() == "set-cookie":
                    return [
                        "sessionid=abc; Path=/",
                        "csrftoken=def; Path=/",
                    ]
                return []

        response = FakeResponse(
            headers={"Set-Cookie": "sessionid=abc, csrftoken=def"},
        )
        response.raw = SimpleNamespace(headers=CombinedCookieHeaders())

        headers = web_search.response_headers_from_upstream(response)

        self.assertEqual(
            [
                ("Set-Cookie", "sessionid=abc; Path=/"),
                ("Set-Cookie", "csrftoken=def; Path=/"),
                ("Content-Type", "text/html"),
            ],
            headers,
        )

    def test_response_with_upstream_headers_preserves_duplicate_headers(self):
        response = web_search.response_with_upstream_headers(
            "redirecting",
            302,
            [
                ("Location", "/dashboard"),
                ("Set-Cookie", "sessionid=abc; Path=/"),
                ("Set-Cookie", "csrftoken=def; Path=/"),
            ],
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/dashboard")
        raw_headers = getattr(response, "raw_headers", [])
        if raw_headers:
            self.assertIn((b"set-cookie", b"sessionid=abc; Path=/"), raw_headers)
            self.assertIn((b"set-cookie", b"csrftoken=def; Path=/"), raw_headers)

    def test_response_with_upstream_headers_mutates_raw_headers_in_place(self):
        class RawHeaderResponse:
            latest = None

            def __init__(self, content, status_code=200):
                self.body = str(content).encode("utf-8")
                self.status_code = status_code
                self.raw_headers = [(b"content-length", str(len(self.body)).encode())]
                self.original_raw_headers = self.raw_headers
                self.headers = {}
                RawHeaderResponse.latest = self

        with patch("web_search.Response", RawHeaderResponse):
            response = web_search.response_with_upstream_headers(
                "redirecting",
                302,
                [
                    ("Set-Cookie", "sessionid=abc; Path=/"),
                    ("Set-Cookie", "csrftoken=def; Path=/"),
                ],
            )

        self.assertIs(response.raw_headers, response.original_raw_headers)
        self.assertIn((b"set-cookie", b"sessionid=abc; Path=/"), response.raw_headers)
        self.assertIn((b"set-cookie", b"csrftoken=def; Path=/"), response.raw_headers)

    def test_response_with_upstream_headers_replaces_default_content_type(self):
        class DefaultContentTypeResponse:
            def __init__(self, content, status_code=200):
                self.body = str(content).encode("utf-8")
                self.status_code = status_code
                self.raw_headers = [
                    (b"content-length", str(len(self.body)).encode()),
                    (b"content-type", b"text/plain; charset=utf-8"),
                ]
                self.headers = {}

        with patch("web_search.Response", DefaultContentTypeResponse):
            response = web_search.response_with_upstream_headers(
                "<html></html>",
                200,
                [("Content-Type", "text/html; charset=utf-8")],
            )

        content_type_headers = [
            header for header in response.raw_headers if header[0] == b"content-type"
        ]
        self.assertEqual(
            [(b"content-type", b"text/html; charset=utf-8")],
            content_type_headers,
        )

    @patch("web_search.requests.get")
    def test_paperless_ui_proxy_injects_script_and_forwards_cookie(self, get):
        get.return_value = FakeResponse(
            200,
            text="<html><body><pngx-root></pngx-root></body></html>",
            headers={"Content-Type": "text/html; charset=utf-8"},
        )
        request = SimpleNamespace(
            headers={
                "accept": "text/html",
                "cookie": "sessionid=abc",
                "user-agent": "Browser",
            },
            path_params={"path": "dashboard"},
            url=SimpleNamespace(query="view=all"),
        )

        response = web_search.paperless_ui_proxy(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn(web_search.PAPERLESS_UI_SCRIPT_PATH, response.body.decode())
        get.assert_called_once()
        self.assertEqual(
            get.call_args.args[0],
            f"{web_search.config.PAPERLESS_API_URL}/dashboard?view=all",
        )
        self.assertEqual(get.call_args.kwargs["headers"]["Cookie"], "sessionid=abc")
        self.assertFalse(get.call_args.kwargs["allow_redirects"])

    @patch("web_search.requests.get")
    def test_paperless_ui_proxy_handles_root_path(self, get):
        get.return_value = FakeResponse(
            200,
            text="<html><body></body></html>",
            headers={"Content-Type": "text/html"},
        )
        request = SimpleNamespace(
            headers={"accept": "text/html"},
            path_params={"path": ""},
            url=SimpleNamespace(query=""),
        )

        web_search.paperless_ui_proxy(request)

        self.assertEqual(
            get.call_args.args[0],
            f"{web_search.config.PAPERLESS_API_URL}/",
        )

    @patch("web_search.requests.get")
    def test_paperless_ui_proxy_preserves_redirect_without_injection(self, get):
        get.return_value = FakeResponse(
            302,
            text="",
            headers={"Location": "/accounts/login/?next=/dashboard"},
        )
        request = SimpleNamespace(
            headers={"accept": "text/html"},
            path_params={"path": "dashboard"},
            url=SimpleNamespace(query=""),
        )

        response = web_search.paperless_ui_proxy(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.headers["Location"],
            "/accounts/login/?next=/dashboard",
        )
        self.assertNotIn(web_search.PAPERLESS_UI_SCRIPT_PATH, response.body.decode())

    @patch("web_search.requests.get", side_effect=requests.Timeout())
    def test_paperless_ui_proxy_uses_ui_specific_error_response(self, _get):
        request = SimpleNamespace(
            headers={"accept": "text/html"},
            path_params={"path": "dashboard"},
            url=SimpleNamespace(query=""),
        )

        response = web_search.paperless_ui_proxy(request)

        self.assertEqual(response.status_code, 503)
        self.assertIn("Paperless-ngx is temporarily unavailable", response.body.decode())
        self.assertNotIn("Search could not verify", response.body.decode())

    @patch("web_search.requests.get")
    def test_paperless_ui_proxy_rejects_denied_internal_paths(self, get):
        request = SimpleNamespace(
            headers={"accept": "application/json"},
            path_params={"path": "api/documents/"},
            url=SimpleNamespace(query=""),
        )

        response = web_search.paperless_ui_proxy(request)

        self.assertEqual(response.status_code, 404)
        get.assert_not_called()

    @patch("web_search.requests.get")
    def test_paperless_ui_proxy_rejects_traversal_paths(self, get):
        unsafe_paths = [
            "../api/documents/",
            "dashboard/../api/documents/",
            "%2e%2e/api/documents/",
            "dashboard/%2e%2e/api/documents/",
            "dashboard\\api",
            "dashboard/%5capi",
            "%2fapi/documents/",
        ]
        for unsafe_path in unsafe_paths:
            with self.subTest(unsafe_path=unsafe_path):
                request = SimpleNamespace(
                    headers={"accept": "text/html"},
                    path_params={"path": unsafe_path},
                    url=SimpleNamespace(query=""),
                )

                response = web_search.paperless_ui_proxy(request)

                self.assertEqual(response.status_code, 404)
        get.assert_not_called()

    @patch("web_search.requests.get")
    def test_paperless_ui_proxy_skips_non_html_response(self, get):
        get.return_value = FakeResponse(
            200,
            text='{"ok": true}',
            headers={"Content-Type": "application/json"},
        )
        request = SimpleNamespace(
            headers={"accept": "application/json"},
            path_params={"path": "dashboard"},
            url=SimpleNamespace(query=""),
        )

        response = web_search.paperless_ui_proxy(request)

        self.assertEqual(response.status_code, 200)
        self.assertNotIn(web_search.PAPERLESS_UI_SCRIPT_PATH, response.body.decode())

    @patch("web_search.config.MCP_AUTH_TOKEN", "paperless-ai-token")
    @patch(
        "web_search.validate_paperless_session",
        return_value={"username": "admin", "is_superuser": True},
    )
    def test_mcp_config_api_returns_token_for_admin_session(self, _validate):
        request = SimpleNamespace(headers={"cookie": "sessionid=abc"})

        response = web_search.mcp_config_api(request)
        payload = json.loads(response.body)

        self.assertEqual(payload["server_name"], "paperless-ai")
        self.assertEqual(payload["endpoint_path"], "/mcp")
        self.assertEqual(payload["auth_token"], "paperless-ai-token")
        self.assertTrue(payload["can_view_token"])
        self.assertTrue(payload["token_available"])
        self.assertTrue(payload["token_configured"])

    @patch("web_search.config.MCP_AUTH_TOKEN", "paperless-ai-token")
    @patch(
        "web_search.validate_paperless_session",
        return_value={"username": "viewer", "is_superuser": False, "is_staff": False},
    )
    def test_mcp_config_api_hides_token_for_non_admin_session(self, _validate):
        request = SimpleNamespace(headers={"cookie": "sessionid=abc"})

        response = web_search.mcp_config_api(request)
        payload = json.loads(response.body)

        self.assertIsNone(payload["auth_token"])
        self.assertFalse(payload["can_view_token"])
        self.assertFalse(payload["token_available"])
        self.assertTrue(payload["token_configured"])

    @patch("web_search.config.MCP_AUTH_TOKEN", "paperless-ai-token")
    @patch(
        "web_search.validate_paperless_session",
        return_value={"username": "staff", "is_superuser": False, "is_staff": True},
    )
    def test_mcp_config_api_hides_token_for_staff_session(self, _validate):
        request = SimpleNamespace(headers={"cookie": "sessionid=abc"})

        response = web_search.mcp_config_api(request)
        payload = json.loads(response.body)

        self.assertIsNone(payload["auth_token"])
        self.assertFalse(payload["can_view_token"])
        self.assertFalse(payload["token_available"])
        self.assertTrue(payload["token_configured"])

    @patch("web_search.validate_paperless_session", return_value=None)
    def test_mcp_page_uses_paperless_login_redirect(self, _validate):
        request = SimpleNamespace(
            headers={"cookie": ""},
            url=SimpleNamespace(path="/search/mcp", query=""),
        )

        response = web_search.mcp_page(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            response.headers["location"],
            "/accounts/login/?next=%2Fsearch%2Fmcp",
        )


class ConfigTests(unittest.TestCase):
    @patch.dict(os.environ, {"TEST_FLOAT": "nan"})
    def test_env_float_rejects_nan(self):
        with self.assertRaises(SystemExit):
            config._env_float("TEST_FLOAT", "0")

    @patch.dict(os.environ, {"TEST_FLOAT": "inf"})
    def test_env_float_rejects_infinity(self):
        with self.assertRaises(SystemExit):
            config._env_float("TEST_FLOAT", "0")


class SessionSearchTests(unittest.TestCase):
    @patch("search.requests.request")
    def test_paperless_session_request_copies_caller_headers(self, request):
        caller_headers = {"X-Test": "yes"}

        search.paperless_session_request(
            "GET",
            "/api/documents/",
            "sessionid=abc",
            headers=caller_headers,
        )

        self.assertEqual(caller_headers, {"X-Test": "yes"})
        sent_headers = request.call_args.kwargs["headers"]
        self.assertEqual(sent_headers["X-Test"], "yes")
        self.assertEqual(sent_headers["Accept"], "application/json")
        self.assertEqual(sent_headers["Cookie"], "sessionid=abc")

    @patch("search.paperless_session_request")
    def test_get_documents_for_session_batches_large_candidate_sets(self, paperless_request):
        def response_for(method, path, cookie_header, **kwargs):
            self.assertEqual(method, "GET")
            self.assertEqual(path, "/api/documents/")
            self.assertEqual(cookie_header, "sessionid=abc")
            ids = [
                int(doc_id)
                for doc_id in kwargs["params"]["id__in"].split(",")
            ]
            self.assertLessEqual(kwargs["params"]["page_size"], 100)
            self.assertIn("title", kwargs["params"]["fields"])
            return FakeResponse(200, {"results": [{"id": doc_id} for doc_id in ids]})

        paperless_request.side_effect = response_for

        results = search.get_documents_for_session(
            list(range(1, 206)),
            "sessionid=abc",
        )

        self.assertEqual(len(results), 205)
        self.assertEqual(paperless_request.call_count, 3)

    @patch("search.paperless_session_request")
    def test_keyword_search_for_session_requests_card_fields(self, paperless_request):
        paperless_request.return_value = FakeResponse(
            200,
            {
                "results": [
                    {
                        "id": 7,
                        "title": "Crop plan",
                        "created_date": "2026-01-02",
                        "content": "Crop plan notes from Paperless",
                    },
                ],
            },
        )

        results = search.keyword_search_for_session(
            "crop",
            limit=12,
            cookie_header="sessionid=abc",
        )

        self.assertEqual(results[0]["document_url"], "/documents/7")
        self.assertEqual(results[0]["matched_chunk"], "Crop plan notes from Paperless")
        self.assertEqual(results[0]["sources"], ["keyword"])
        _method, _path, _cookie_header = paperless_request.call_args.args
        params = paperless_request.call_args.kwargs["params"]
        self.assertEqual(params["query"], "crop")
        self.assertEqual(params["page_size"], 12)
        self.assertEqual(params["fields"], search.PAPERLESS_KEYWORD_DOCUMENT_FIELDS)
        self.assertEqual(params["truncate_content"], "true")

    @patch("search.embeddings.get_embedding", return_value=[0.1, 0.2])
    @patch("search.db.search_similar_documents")
    @patch("search.get_documents_for_session")
    def test_semantic_search_filters_before_returning_chunks(
        self,
        get_documents,
        search_similar,
        _get_embedding,
    ):
        search_similar.return_value = [
            {
                "document_id": 1,
                "chunk_index": 0,
                "chunk_text": "authorized soil test chunk",
                "similarity": 0.9,
            },
            {
                "document_id": 2,
                "chunk_index": 0,
                "chunk_text": "secret unauthorized chunk",
                "similarity": 0.8,
            },
        ]
        get_documents.return_value = {1: {"id": 1, "title": "Soil Test"}}

        results = search.semantic_search_for_session(
            "soil",
            limit=10,
            cookie_header="sessionid=abc",
        )

        self.assertEqual([result["id"] for result in results], [1])
        self.assertEqual(results[0]["matched_chunk"], "authorized soil test chunk")
        self.assertNotIn("secret unauthorized chunk", json.dumps(results))
        get_documents.assert_called_once_with([1, 2], "sessionid=abc")

    @patch("search.embeddings.get_embedding", return_value=[0.1, 0.2])
    @patch("search.db.search_similar_documents")
    @patch("search.get_documents_for_session")
    def test_semantic_search_drops_low_similarity_candidates(
        self,
        get_documents,
        search_similar,
        _get_embedding,
    ):
        search_similar.return_value = [
            {
                "document_id": 7,
                "chunk_index": 0,
                "chunk_text": "nearest but irrelevant chunk",
                "similarity": search.config.SEMANTIC_MIN_SIMILARITY - 0.01,
            },
        ]

        results = search.semantic_search_for_session(
            "zzzxxy-nomatch-term-12345",
            limit=10,
            cookie_header="sessionid=abc",
        )

        self.assertEqual(results, [])
        get_documents.assert_not_called()

    @patch("search.embeddings.get_embedding", return_value=[0.1, 0.2])
    @patch("search.db.search_similar_documents")
    @patch("search.get_documents_for_session")
    def test_semantic_search_expands_until_authorized_results_are_found(
        self,
        get_documents,
        search_similar,
        _get_embedding,
    ):
        first_page = [
            {
                "document_id": doc_id,
                "chunk_index": 0,
                "chunk_text": f"unauthorized chunk {doc_id}",
                "similarity": 1.0 - doc_id / 100,
            }
            for doc_id in range(1, 21)
        ]
        second_page = first_page + [
            {
                "document_id": 99,
                "chunk_index": 0,
                "chunk_text": "authorized late chunk",
                "similarity": 0.5,
            }
        ]
        search_similar.side_effect = [first_page, second_page]

        def authorized_for(doc_ids, _cookie_header):
            if 99 in doc_ids:
                return {99: {"id": 99, "title": "Late Match"}}
            return {}

        get_documents.side_effect = authorized_for

        results = search.semantic_search_for_session(
            "late",
            limit=1,
            cookie_header="sessionid=abc",
        )

        self.assertEqual([result["id"] for result in results], [99])
        self.assertEqual(results[0]["matched_chunk"], "authorized late chunk")
        self.assertEqual(
            [call.kwargs["limit"] for call in search_similar.call_args_list],
            [20, 40],
        )

    @patch("search.config.SEMANTIC_MIN_SIMILARITY", -1)
    @patch("search.embeddings.get_embedding", return_value=[0.1, 0.2])
    @patch("search.db.search_similar_documents")
    @patch("search.get_documents_for_session")
    def test_semantic_search_handles_malformed_similarity(
        self,
        get_documents,
        search_similar,
        _get_embedding,
    ):
        search_similar.return_value = [
            {
                "document_id": 1,
                "chunk_index": 0,
                "chunk_text": "authorized chunk",
                "similarity": "not-a-float",
            },
        ]
        get_documents.return_value = {1: {"id": 1, "title": "Authorized"}}

        results = search.semantic_search_for_session(
            "authorized",
            limit=1,
            cookie_header="sessionid=abc",
        )

        self.assertEqual(results[0]["similarity"], 0.0)

    @patch("search.keyword_search_for_session")
    @patch("search.semantic_search_for_session")
    def test_hybrid_search_merges_sources_and_scores(self, semantic, keyword):
        semantic.return_value = [
            {"id": 1, "title": "A", "document_url": "/documents/1", "sources": ["semantic"]},
            {"id": 2, "title": "B", "document_url": "/documents/2", "sources": ["semantic"]},
        ]
        keyword.return_value = [
            {"id": 1, "title": "A", "document_url": "/documents/1", "sources": ["keyword"]},
            {"id": 3, "title": "C", "document_url": "/documents/3", "sources": ["keyword"]},
        ]

        results = search.hybrid_search_for_session("crop", limit=10, cookie_header="sessionid=abc")
        by_id = {result["id"]: result for result in results}

        self.assertEqual(by_id[1]["sources"], ["keyword", "semantic"])
        self.assertGreater(by_id[1]["relevance_score"], by_id[2]["relevance_score"])
        self.assertEqual(by_id[3]["document_url"], "/documents/3")


if __name__ == "__main__":
    unittest.main()
