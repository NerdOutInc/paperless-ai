import secrets
from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send
import search
import db
import config


class BearerTokenMiddleware:
    """ASGI middleware that validates a static Bearer token."""

    def __init__(self, app: ASGIApp, token: str, protected_prefixes=("/mcp",)):
        self.app = app
        self.token = token
        self.protected_prefixes = protected_prefixes

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] in ("http", "websocket"):
            path = scope.get("path", "")
            protected = any(
                path == prefix or path.startswith(f"{prefix}/")
                for prefix in self.protected_prefixes
            )
            if protected:
                headers = dict(scope.get("headers", []))
                auth = headers.get(b"authorization", b"").decode()
                if not auth.startswith("Bearer ") or not secrets.compare_digest(
                    auth[7:], self.token
                ):
                    if scope["type"] == "http":
                        resp = JSONResponse({"error": "unauthorized"}, status_code=401)
                        await resp(scope, receive, send)
                        return
                    # Reject WebSocket upgrades
                    await send({"type": "websocket.close", "code": 4401})
                    return
        await self.app(scope, receive, send)


mcp = FastMCP(
    "Paperless Ag",
    streamable_http_path="/mcp",
    json_response=True,
    stateless_http=True,
    host="0.0.0.0",
)


@mcp.tool()
def search_documents(query: str, limit: int = 10) -> list:
    """Search farm documents using hybrid semantic and keyword search.

    Combines vector similarity search (finds conceptually related documents)
    with keyword search (finds exact term matches). Use this for queries like
    "find everything related to nitrogen management" or "crop insurance documents".

    Args:
        query: Natural language search query
        limit: Maximum number of results (default 10)
    """
    limit = max(1, min(limit, 100))
    return search.hybrid_search(query, limit=limit)


@mcp.tool()
def get_document(document_id: int) -> dict:
    """Get full details and content for a specific document.

    Use this after searching to read the complete text of a document.

    Args:
        document_id: The Paperless document ID
    """
    if document_id < 1:
        return {"error": "document_id must be a positive integer"}
    return search.get_document(document_id)


@mcp.tool()
def list_tags() -> list:
    """List all tags in the document management system.

    Returns all available tags. Useful for understanding how documents
    are organized and for filtering searches.
    """
    return search.list_tags()


@mcp.tool()
def list_document_types() -> list:
    """List all document types in the system.

    Returns categories like Soil Test Report, Crop Insurance Policy, etc.
    """
    return search.list_document_types()


@mcp.tool()
def search_by_tag(tag: str, limit: int = 20) -> list:
    """Find all documents with a specific tag.

    Args:
        tag: Tag name (e.g., horob-family-farms, corn, nitrogen)
        limit: Maximum number of results
    """
    limit = max(1, min(limit, 100))
    return search.search_by_tag(tag, limit=limit)


@mcp.tool()
def search_by_date_range(start: str, end: str, limit: int = 20) -> list:
    """Find documents within a date range.

    Args:
        start: Start date in YYYY-MM-DD format
        end: End date in YYYY-MM-DD format
        limit: Maximum number of results
    """
    limit = max(1, min(limit, 100))
    return search.search_by_date_range(start, end, limit=limit)


@mcp.tool()
def get_embedding_status() -> dict:
    """Check the status of document embeddings.

    Returns how many documents and chunks have been embedded so far.
    """
    return db.get_embedding_stats()
