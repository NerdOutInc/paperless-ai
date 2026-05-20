#!/usr/bin/env bash
set -euo pipefail
umask 077
if ! cd /opt/paperless-ag 2>/dev/null; then
    echo "Could not enter /opt/paperless-ag" >&2
    exit 1
fi

mkdir -p backups
caddyfile_changed=false

add_search_route_to_caddyfile() {
    local tmp
    tmp=$(mktemp)
    if awk '
        BEGIN { inserted = 0 }
        /^[[:space:]]*handle[[:space:]]*\{$/ && !inserted {
            print "    @search path /search /search/*"
            print "    handle @search {"
            print "        reverse_proxy companion:3001 {"
            print "            header_up Host localhost:3001"
            print "        }"
            print "    }"
            inserted = 1
        }
        { print }
        END { if (!inserted) exit 1 }
    ' Caddyfile > "$tmp"; then
        mv "$tmp" Caddyfile
        return 0
    fi
    rm -f "$tmp"
    return 1
}

add_paperless_ui_route_to_caddyfile() {
    local tmp
    tmp=$(mktemp)
    if awk '
        BEGIN { inserted = 0 }
        /^[[:space:]]*handle[[:space:]]*\{$/ && !inserted {
            print "    @paperless_ui {"
            print "        method GET"
            print "        header Accept *text/html*"
            print "        not path /api /api/* /static /static/* /media /media/* /accounts /accounts/* /search /search/* /mcp /mcp/* /paperless-ui-proxy /paperless-ui-proxy/* /.well-known /.well-known/*"
            print "    }"
            print "    handle @paperless_ui {"
            print "        rewrite * /paperless-ui-proxy{uri}"
            print "        reverse_proxy companion:3001 {"
            print "            header_up Host localhost:3001"
            print "        }"
            print "    }"
            inserted = 1
        }
        { print }
        END { if (!inserted) exit 1 }
    ' Caddyfile > "$tmp"; then
        mv "$tmp" Caddyfile
        return 0
    fi
    rm -f "$tmp"
    return 1
}

if docker compose ps --status running db 2>/dev/null | grep -q db; then
    echo "Backing up database before update..."
    docker compose exec -T db pg_dump --clean -U paperless paperless \
        > "backups/pre-update-$(date +%Y%m%d-%H%M%S).sql"
    echo "[OK] Database backed up"
else
    echo "[!] Database not running -- skipping backup"
fi

if [[ -f Caddyfile ]] && ! grep -q '@search path' Caddyfile; then
    if add_search_route_to_caddyfile; then
        echo "[OK] Caddyfile search route added"
        caddyfile_changed=true
    else
        echo "[!] Could not find the fallback handle block in Caddyfile; add /search routing manually."
    fi
fi
if [[ -f Caddyfile ]] && ! grep -q '@paperless_ui' Caddyfile; then
    if add_paperless_ui_route_to_caddyfile; then
        echo "[OK] Caddyfile Paperless UI link route added"
        caddyfile_changed=true
    else
        echo "[!] Could not find the fallback handle block in Caddyfile; add the Paperless UI link route manually."
    fi
fi

echo "Pulling latest images..."
docker compose pull

echo "Restarting services..."
docker compose up -d

if [[ "$caddyfile_changed" == "true" ]]; then
    echo "Reloading Caddy..."
    docker compose exec -T caddy caddy reload --config /etc/caddy/Caddyfile \
        || docker compose restart caddy
fi

echo ""
echo "[OK] Update complete. Check your Paperless UI to confirm."
