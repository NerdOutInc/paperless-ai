:80 {
    header {
        X-Frame-Options DENY
        X-Content-Type-Options nosniff
        Referrer-Policy strict-origin-when-cross-origin
    }

    @discovery path /.well-known/oauth-authorization-server /.well-known/openid-configuration
    handle @discovery {
        respond 404
    }

    @mcp path /mcp /mcp/*
    handle @mcp {
        reverse_proxy companion:3001 {
            header_up Host localhost:3001
        }
    }

    @search path /search /search/*
    handle @search {
        reverse_proxy companion:3001 {
            header_up Host localhost:3001
        }
    }

    handle {
        reverse_proxy paperless:8000
    }
}
