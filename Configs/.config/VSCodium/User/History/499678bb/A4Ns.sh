#!/usr/bin/env bash
set -euo pipefail

# -----------------------------
# Idle Manager Toggle/Runner
# Supports: hypridle, swayidle
# Status file: ~/.cache/idle-manager.status
# Values: activated | deactivated
# -----------------------------

STATUS_FILE="${XDG_CACHE_HOME:-$HOME/.cache}/idle-manager.status"

# 1) Detect available idle manager
IDLE_BIN=""
if command -v hypridle >/dev/null 2>&1; then
  IDLE_BIN="hypridle"
elif command -v swayidle >/dev/null 2>&1; then
  IDLE_BIN="swayidle"
else
  echo "Neither hypridle nor swayidle is installed."
  exit 1
fi

# 2) Create cache status file if missing (default: activated)
mkdir -p "$(dirname "$STATUS_FILE")"
if [[ ! -f "$STATUS_FILE" ]]; then
  echo "activated" > "$STATUS_FILE"
fi

# 3) Read status
STATUS="$(tr -d ' \t\r\n' < "$STATUS_FILE" | tr '[:upper:]' '[:lower:]')"
# Normalize some common variants
case "$STATUS" in
  activated|active|on|1|true|yes) STATUS="activated" ;;
  deactivated|inactive|off|0|false|no) STATUS="deactivated" ;;
  *) 
    echo "Unknown status in $STATUS_FILE: '$STATUS' (expected activated/deactivated)"
    exit 2
    ;;
esac

# Helper: check if idle manager is already running
is_running() {
  pgrep -x "$IDLE_BIN" >/dev/null 2>&1
}

# Helper: stop idle manager
stop_idle() {
  if is_running; then
    pkill -x "$IDLE_BIN" || true
  fi
}

# Helper: start idle manager
start_idle() {
  if is_running; then
    return 0
  fi

  # Start in background, detached from terminal
  # NOTE: swayidle typically needs arguments to do anything useful.
  # If you already run swayidle with args elsewhere, keep them there and let this script only manage processes.
  if [[ "$IDLE_BIN" == "hypridle" ]]; then
    nohup hypridle >/dev/null 2>&1 &
  else
    # Minimal no-op run (won't lock/suspend without args). Replace with your preferred swayidle config/args.
    # Example:
    # nohup swayidle -w timeout 300 'swaylock -f' timeout 600 'systemctl suspend' >/dev/null 2>&1 &
    nohup swayidle -w >/dev/null 2>&1 &
  fi
}

# 4) Apply desired state
if [[ "$STATUS" == "activated" ]]; then
  start_idle
else
  stop_idle
fi

