#!/usr/bin/env bash
set -euo pipefail

# Regenerate missing SSH host keys (cleared during snapshot build)
ssh-keygen -A
systemctl restart ssh

# Generate a one-time setup token and persist it for the setup API
SETUP_TOKEN=$(head -c 48 /dev/urandom | base64 | tr -dc 'a-zA-Z0-9' | head -c 32)
echo "$SETUP_TOKEN" > /opt/paperless-ag/.setup-token
chmod 600 /opt/paperless-ag/.setup-token

# Start the setup wizard services
systemctl start paperless-setup-api.service
systemctl start paperless-setup.service

# Show the setup token on the droplet console and MOTD
cat <<MSG

============================================================
 Paperless AI setup wizard is ready on port 80.

 Your one-time setup token:  $SETUP_TOKEN

 Enter this token in the web wizard to authorize setup.
============================================================

MSG

# Also add to MOTD so it shows on SSH login
cat > /etc/update-motd.d/99-paperless-setup <<MOTD
#!/bin/sh
echo ""
echo "Paperless AI setup token: $SETUP_TOKEN"
echo "Open http://\$(curl -s -4 http://169.254.169.254/metadata/v1/interfaces/public/0/ipv4/address) to begin setup."
echo ""
MOTD
chmod 755 /etc/update-motd.d/99-paperless-setup
