#!/usr/bin/env bash

set -euo pipefail

STATUS_FILE="${XDG_CACHE_HOME:-$HOME/.cache}/idle_manager.status"

usage() {
  echo "Usage: $(basename "$0") <activated|deactivated>"
  exit 2
}

# 1) Detect idle manager (prefer hypridle if both exist)
if command -v hypridle >/dev/null 2>&1; then
  IDLE_BIN="hypridle"
elif command -v swayidle >/dev/null 2>&1; then
  IDLE_BIN="swayidle"
else
  echo "Error: neither hypridle nor swayidle is installed."
  exit 1
fi

# Require exactly 1 argument
[[ $# -eq 1 ]] || usage

arg="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | tr -d ' \t\r\n')"

# Normalize argument
case "$arg" in
  activated|active|on|1|true|yes) status="activated" ;;
  deactivated|deactivate|inactive|off|0|false|no) status="deactivated" ;;
  *) echo "Error: invalid argument '$1' (expected: activated | deactivated)"; usage ;;
esac

# Ensure cache dir exists + write status
mkdir -p "$(dirname "$STATUS_FILE")"
echo "$status" > "$STATUS_FILE"

is_running() { pgrep -x "$IDLE_BIN" >/dev/null 2>&1; }

stop_idle() {
  # Don't fail if not running
  pkill -x "$IDLE_BIN" >/dev/null 2>&1 || true
}

start_idle() {
  # Avoid duplicates
  if is_running; then return 0; fi

  if [[ "$IDLE_BIN" == "hypridle" ]]; then
    nohup hypridle >/dev/null 2>&1 &
  else
    # NOTE: swayidle needs args to do real actions (lock/suspend). Replace with your config/args.
    # Example:
    # nohup swayidle -w timeout 300 'swaylock -f' timeout 600 'systemctl suspend' >/dev/null 2>&1 &
    nohup swayidle -w >/dev/null 2>&1 &
  fi
}

# 2) Apply requested status
if [[ "$status" == "activated" ]]; then
  start_idle
else
  stop_idle
fi
