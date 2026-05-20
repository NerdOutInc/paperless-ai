#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${PAPERLESS_AI_ROOT:-$(cd -- "$SCRIPT_DIR/../.." && pwd)}"
SKILL_DIR="${SCREEN_STUDIO_SKILL_DIR:-$ROOT/../ai-skills/screen-studio}"
CLICLICK="${CLICLICK:-/opt/homebrew/bin/cliclick}"
SCROLL_WHEEL="${SCREEN_STUDIO_SCROLL_WHEEL:-$SKILL_DIR/scripts/scroll-wheel.swift}"
DOCKER_URL="https://www.docker.com/products/docker-desktop/"
DOCKER_PS_COMMAND='docker ps --filter name=paperless-ai --format "table {{.Names}}\t{{.Status}}"'

hide_process() {
  local name="$1"
  osascript - "$name" <<'APPLESCRIPT' >/dev/null 2>&1 || true
on run argv
  set processName to item 1 of argv
  tell application "System Events"
    if exists process processName then
      set visible of process processName to false
    end if
  end tell
end run
APPLESCRIPT
}

terminal_script() {
  osascript - "$1" <<'APPLESCRIPT'
on run argv
  set shellText to item 1 of argv
  tell application "Terminal"
    activate
    if not (exists window 1) then
      do script shellText
    else
      do script shellText in front window
    end if
  end tell
end run
APPLESCRIPT
}

keystroke_terminal() {
  osascript - "$1" <<'APPLESCRIPT'
on run argv
  set textToType to item 1 of argv
  tell application "Terminal" to activate
  delay 0.25
  tell application "System Events"
    keystroke textToType
    delay 0.1
    key code 36
  end tell
end run
APPLESCRIPT
}

activate_app() {
  osascript - "$1" <<'APPLESCRIPT'
on run argv
  tell application (item 1 of argv) to activate
end run
APPLESCRIPT
}

type_in_terminal() {
  osascript - "$1" <<'APPLESCRIPT'
on run argv
  set textToType to item 1 of argv
  tell application "Terminal" to activate
  delay 0.25
  tell application "System Events"
    repeat with c in characters of textToType
      keystroke c
      delay 0.018
    end repeat
    delay 0.15
    key code 36
  end tell
end run
APPLESCRIPT
}

case "${1:-}" in
  reset)
    osascript -e 'tell application "Helium" to quit' >/dev/null 2>&1 || true
    sleep 0.5
    open -a Helium "$DOCKER_URL"
    sleep 2
    activate_app "Helium"
    osascript <<'APPLESCRIPT' >/dev/null 2>&1 || true
tell application "System Events"
  key code 115
end tell
APPLESCRIPT
    open "docker-desktop://dashboard/containers" >/dev/null 2>&1 || true
    open -a "Docker Desktop"
    terminal_script "cd '$ROOT'; clear; export PS1='> '; printf 'Ready to show running Docker containers.\\n\\n'; pwd"
    sleep 1
    hide_process "Docker Desktop"
    hide_process "Terminal"
    hide_process "Codex"
    activate_app "Helium"
    ;;
  reset-retake)
    osascript -e 'tell application "Helium" to quit' >/dev/null 2>&1 || true
    sleep 0.5
    open -a Helium "$DOCKER_URL"
    sleep 3
    activate_app "Helium"
    osascript <<'APPLESCRIPT' >/dev/null 2>&1 || true
tell application "System Events"
  key code 115
end tell
APPLESCRIPT
    open "docker-desktop://dashboard/containers" >/dev/null 2>&1 || true
    open -a "Docker Desktop"
    activate_app "Terminal"
    osascript <<'APPLESCRIPT' >/dev/null 2>&1 || true
tell application "System Events"
  keystroke "k" using command down
end tell
APPLESCRIPT
    keystroke_terminal "cd '$ROOT'"
    sleep 0.8
    keystroke_terminal "clear"
    sleep 1
    hide_process "Docker Desktop"
    hide_process "Terminal"
    hide_process "Codex"
    activate_app "Helium"
    "$CLICLICK" -e 250 m:825,470
    ;;
  site)
    activate_app "Helium"
    ;;
  scroll-site)
    activate_app "Helium"
    sleep 0.2
    "$CLICLICK" -e 300 m:825,470 c:.
    sleep 0.2
    "$SCROLL_WHEEL" trackpad 1 down 0.045 0.24 "4,8,14,22,30,22,14,8,4"
    ;;
  scroll-product-page)
    activate_app "Helium"
    sleep 0.2
    "$CLICLICK" -e 250 m:825,470 c:.
    osascript <<'APPLESCRIPT' >/dev/null 2>&1 || true
tell application "System Events"
  key code 115
end tell
APPLESCRIPT
    sleep 0.2
    "$SCROLL_WHEEL" trackpad 28 down 0.02 0.18 "5,10,18,28,40,54,64,54,40,28,18,10,5"
    ;;
  desktop)
    open "docker-desktop://dashboard/containers" >/dev/null 2>&1 || true
    activate_app "Docker Desktop"
    ;;
  desktop-clear-cursor)
    open "docker-desktop://dashboard/containers" >/dev/null 2>&1 || true
    activate_app "Docker Desktop"
    sleep 1
    "$CLICLICK" -e 250 m:80,900
    ;;
  terminal)
    activate_app "Terminal"
    ;;
  run-docker-ps)
    type_in_terminal "$DOCKER_PS_COMMAND"
    ;;
  final)
    hide_process "Terminal"
    activate_app "Docker Desktop"
    ;;
  hide-workbench)
    hide_process "Codex"
    hide_process "Code"
    hide_process "Xcode"
    ;;
  *)
    echo "usage: $0 reset|reset-retake|site|scroll-site|scroll-product-page|desktop|desktop-clear-cursor|terminal|run-docker-ps|final|hide-workbench" >&2
    exit 64
    ;;
esac
