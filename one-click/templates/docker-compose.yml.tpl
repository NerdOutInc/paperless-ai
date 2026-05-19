services:
  db:
    image: pgvector/pgvector:pg16
    restart: unless-stopped
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: paperless
      POSTGRES_USER: paperless
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U paperless"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  paperless:
    image: ghcr.io/paperless-ngx/paperless-ngx:latest
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - paperless-data:/usr/src/paperless/data
      - paperless-media:/usr/src/paperless/media
      - paperless-export:/usr/src/paperless/export
      - paperless-consume:/usr/src/paperless/consume
    environment:
      PAPERLESS_REDIS: redis://redis:6379
      PAPERLESS_DBHOST: db
      PAPERLESS_DBNAME: paperless
      PAPERLESS_DBUSER: paperless
      PAPERLESS_DBPASS: ${DB_PASSWORD}
      PAPERLESS_SECRET_KEY: ${SECRET_KEY}
      PAPERLESS_TIME_ZONE: ${TIMEZONE}
      PAPERLESS_URL: ${PAPERLESS_URL}
      PAPERLESS_ADMIN_USER: ${ADMIN_USER}
      PAPERLESS_ADMIN_PASSWORD: ${ADMIN_PASSWORD}
    healthcheck:
      test: ["CMD", "curl", "-fs", "http://localhost:8000"]
      interval: 30s
      timeout: 10s
      retries: 5
      start_period: 90s

  companion:
    image: ghcr.io/nerdoutinc/paperless-ag:latest
    restart: unless-stopped
    depends_on:
      db:
        condition: service_healthy
      paperless:
        condition: service_healthy
    environment:
      PAPERLESS_API_URL: http://paperless:8000
      PAPERLESS_USERNAME: ${ADMIN_USER}
      PAPERLESS_PASSWORD: ${ADMIN_PASSWORD}
      DATABASE_URL: postgresql://paperless:${DB_PASSWORD}@db:5432/paperless
      EMBEDDING_MODEL: all-MiniLM-L6-v2
      SEMANTIC_MIN_SIMILARITY: "0.25"
      SYNC_INTERVAL_SECONDS: "60"
      MCP_HTTP_PORT: "3001"
      MCP_AUTH_TOKEN: ${MCP_AUTH_TOKEN}
      PYTHONUNBUFFERED: "1"

  caddy:
    image: caddy:2-alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy-data:/data
      - caddy-config:/config
    depends_on:
      - paperless
      - companion

volumes:
  pgdata:
  redisdata:
  paperless-data:
  paperless-media:
  paperless-export:
  paperless-consume:
  caddy-data:
  caddy-config:
