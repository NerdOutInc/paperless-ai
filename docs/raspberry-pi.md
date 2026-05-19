# Install Paperless Ag on a Raspberry Pi

Run Paperless-ngx with semantic search on your home network using a
Raspberry Pi. This guide walks through the full setup -- from flashing the
SD card to searching your documents in the browser.

## What you need

| Item | Minimum | Recommended |
| ---- | ------- | ----------- |
| Raspberry Pi | Pi 4 (4 GB) | Pi 5 (8 GB) |
| Storage | 32 GB microSD | 256 GB+ USB SSD |
| OS | Raspberry Pi OS Lite (64-bit) | same |
| Network | Ethernet or Wi-Fi | Ethernet |
| Power supply | Official USB-C adapter | same |

> **Pi 4 with 2 GB RAM will not work.** Paperless, Postgres, Redis, and the
> embedding model need at least 4 GB to run together.

## 1. Flash Raspberry Pi OS

1. Download [Raspberry Pi Imager](https://www.raspberrypi.com/software/).
2. Choose **Raspberry Pi OS Lite (64-bit)** -- the desktop environment is
   not needed and saves RAM.
3. Click the gear icon and configure:
   - **Hostname:** `paperless` (or whatever you like)
   - **Enable SSH:** yes, use password authentication
   - **Username/password:** pick something secure
   - **Wi-Fi:** enter your network credentials (skip if using Ethernet)
   - **Locale:** set your timezone
4. Flash the SD card (or SSD) and boot the Pi.

## 2. Find your Pi on the network

After booting, find the Pi's IP address. Try any of these from another
computer on the same network:

```bash
# By hostname (if mDNS works on your network)
ping paperless.local

# Or scan your network
# macOS / Linux:
arp -a | grep -i "b8:27:eb\|d8:3a:dd\|dc:a6:32\|e4:5f:01\|2c:cf:67"
```

You can also check your router's admin page for connected devices.

SSH in once you have the IP:

```bash
ssh your-username@paperless.local
# or: ssh your-username@192.168.1.xxx
```

## 3. Boot from USB SSD (recommended)

An SD card works but is slower and less reliable for a database workload.
If you have a USB SSD:

```bash
# Already SSH'd into the Pi
sudo raspi-config
# Advanced Options > Boot Order > USB Boot
# Finish and reboot
```

Then re-flash your SSD with Raspberry Pi Imager (same settings as before)
and boot from it instead.

## 4. Run the install script

From your SSH session on the Pi:

```bash
curl -fsSL https://paperless.fullstack.ag/install.sh | bash
```

The installer will:

1. **Check your system** -- confirms you have enough RAM and disk space.
2. **Install Docker** -- if it's not already installed, the script offers
   to install it for you. Accept the prompt, then log out and back in when
   asked (Docker needs a group change to take effect).

   ```bash
   # After logging back in, run the installer again:
   curl -fsSL https://paperless.fullstack.ag/install.sh | bash
   ```

3. **Ask for configuration** -- since this is a fresh install (no existing
   Paperless), it will prompt for:
   - Admin username and password
   - Timezone
   - Domain name (press Enter to skip -- not needed for local network)
   - Install directory (default: `~/paperless-ag`)
4. **Pull images and start services** -- this downloads about 2 GB of
   container images. On a Pi with a decent internet connection, expect
   5--15 minutes.

When it finishes you'll see a summary with your Paperless URL, Search URL,
and MCP connection details. **Save the MCP auth token** if you plan to
connect AI apps later.

## 5. Access Paperless on your network

Once the installer finishes, Paperless is available at:

```text
http://<your-pi-ip>
```

For example: `http://192.168.1.42` or `http://paperless.local`

Open that URL in a browser on any device on your network. Log in with the
admin username and password you chose during setup.

### Give it a stable IP

Your router probably assigns the Pi a dynamic IP via DHCP. To keep the
address from changing:

1. Open your router's admin page (usually `192.168.1.1`).
2. Find the DHCP reservation or static lease settings.
3. Assign a fixed IP to your Pi's MAC address.

This way `http://192.168.1.42` (or whatever you pick) always works.

## 6. Upload documents

Drag and drop files into the Paperless web UI. Paperless handles OCR
automatically -- you can upload PDFs, images of paper documents, or even
photos from your phone.

The companion container polls for new documents every 60 seconds. After
upload, give it a minute or two to generate embeddings (you can watch
progress in the logs):

```bash
cd ~/paperless-ag && docker compose logs -f companion
```

## 7. Search your documents

Open the Search URL from the install summary:

```text
http://<your-pi-ip>/search
```

Log in with the same Paperless username and password. Search results open in
the normal Paperless document viewer.

For example: `http://192.168.1.42/search` or
`http://paperless.local/search`

## 8. Connect AI apps with MCP

MCP support is optional. It lets AI apps use Paperless Ag's read-only search
tools without exposing Postgres or changing Paperless-ngx.

After installation, log in to Paperless and open:

```text
http://<your-pi-ip>/search/mcp
```

That page shows your MCP server URL, auth token, and current setup instructions
for Claude, Codex, VS Code/Copilot, and llama.cpp.

## 9. Find your MCP token later

If you didn't save the token from the install summary, it's in the `.env`
file:

```bash
grep MCP_AUTH_TOKEN ~/paperless-ag/.env
```

## Day-to-day operations

### Start / stop

```bash
cd ~/paperless-ag
docker compose up -d      # start
docker compose down        # stop
```

Services restart automatically on reboot (`restart: unless-stopped`).

### Update

```bash
bash ~/paperless-ag/update.sh
```

This backs up the database, pulls the latest images, and restarts.

### Backup and restore

```bash
bash ~/paperless-ag/backup.sh                        # manual backup
bash ~/paperless-ag/restore.sh backups/some-file.sql # restore
```

A daily backup runs automatically at 2 AM via cron.

### View logs

```bash
cd ~/paperless-ag
docker compose logs -f              # all services
docker compose logs -f companion    # just the semantic search companion
docker compose logs -f paperless    # just Paperless-ngx
```

## Performance tips

- **Use a USB SSD** instead of an SD card. Postgres performance improves
  dramatically with faster random I/O.
- **Pi 5 with 8 GB** gives the most headroom. The embedding model,
  Postgres, and Paperless all benefit from extra RAM.
- **Ethernet** instead of Wi-Fi reduces latency for the web UI and MCP
  connections.
- **First embedding run is slow.** If you upload many documents at once,
  the initial embedding pass takes a while on ARM. It runs in the
  background and doesn't block Paperless -- just give it time.

## Troubleshooting

### "Not enough RAM" error

You need a Pi 4 or 5 with at least 4 GB RAM. The 2 GB model won't pass
the installer's resource check.

### Docker install asks to log out

This is normal. Docker needs a group change. Log out, SSH back in, and
run the install script again.

### Containers keep restarting

Check logs for the failing service:

```bash
cd ~/paperless-ag && docker compose logs --tail 50 companion
```

Common causes:

- Database not ready yet (give it a minute on first boot)
- Wrong Paperless credentials in `.env`

### Can't reach Paperless from other devices

- Confirm the Pi's IP: `hostname -I`
- Check that port 80 isn't blocked by a firewall: `sudo iptables -L`
- Make sure you're on the same network / subnet as the Pi
