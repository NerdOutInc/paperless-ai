from contextlib import asynccontextmanager
import threading
import time
import uvicorn
import config
import db
import web_search
from worker import EmbeddingWorker
from mcp_server import mcp, BearerTokenMiddleware


def main():
    print("=" * 50)
    print("Paperless Ag Companion Container")
    print("=" * 50)

    # Initialize database (retry in case DB isn't ready yet)
    for attempt in range(15):
        try:
            db.init_db()
            print("Database schema ready.")
            break
        except Exception as e:
            print(f"Waiting for database... (attempt {attempt + 1}): {e}")
            time.sleep(5)
    else:
        print("ERROR: Could not connect to database after 15 attempts")
        return

    # Pre-load the embedding model so it's ready before accepting MCP requests.
    # Without this, the first search request would trigger a model load that
    # can race with the worker thread or hit cache-permission issues.
    import embeddings
    embeddings.load_model()

    # Start embedding worker in background thread
    worker = EmbeddingWorker()
    worker_thread = threading.Thread(target=worker.run, daemon=True, name="embedding-worker")
    worker_thread.start()
    print(f"Embedding worker started (sync every {config.SYNC_INTERVAL}s)")

    # Monitor worker thread health in a separate daemon thread
    def _watch_worker():
        while True:
            time.sleep(60)
            if not worker_thread.is_alive():
                print("WARNING: Embedding worker thread has stopped unexpectedly")
                break

    threading.Thread(target=_watch_worker, daemon=True, name="worker-watchdog").start()

    # Build streamable HTTP app with health endpoint, optionally wrap with auth
    from starlette.applications import Starlette
    from starlette.responses import PlainTextResponse, Response
    from starlette.routing import Mount, Route

    @asynccontextmanager
    async def lifespan(app):
        async with mcp.session_manager.run():
            yield

    routes = [
        Route("/health", lambda r: PlainTextResponse("ok")),
        # Return 404 for OAuth/OIDC discovery so MCP clients skip
        # auth negotiation and use configured Bearer token headers.
        Route("/.well-known/oauth-authorization-server",
              lambda r: Response(status_code=404)),
        Route("/.well-known/openid-configuration",
              lambda r: Response(status_code=404)),
        *web_search.routes(),
        Mount("/", app=mcp.streamable_http_app()),
    ]
    app = Starlette(routes=routes, lifespan=lifespan)
    if config.MCP_AUTH_TOKEN:
        app = BearerTokenMiddleware(
            app,
            config.MCP_AUTH_TOKEN,
            protected_prefixes=("/mcp",),
        )
        print("MCP authentication enabled (Bearer token).")

    # Start MCP server (blocks)
    print(f"Starting MCP server (streamable HTTP) on port {config.MCP_PORT}...")
    uvicorn.run(app, host="0.0.0.0", port=config.MCP_PORT, log_level="warning")


if __name__ == "__main__":
    main()
