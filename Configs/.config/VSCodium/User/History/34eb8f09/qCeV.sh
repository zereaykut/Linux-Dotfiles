#!/usr/bin/env bash
set -euo pipefail

# -----------------------------
# Idle Manager Toggle Script
# -----------------------------

STATUS_FILE="${XDG_CACHE_HOME:-$HOME/.cache}/idle-manager.status"

# 1) Detect idle manager
if command -v hypridle >/dev/null 2>&1; then
  IDLE_BIN="hypridle"
elif command -v swayidle >/dev/null 2>&1; then
  IDLE_BIN="swayidle"
else
  echo "Error: neither hypridle nor swayidle is installed."
  exit 1
fi

# 2) Ensure status file exists (default: activated)
mkdir -p "$(dirname "$STATUS_FILE")"
if [[ ! -f "$STATUS_FILE" ]]; then
  echo "activated" > "$STATUS_FILE"
fi

# 3) Read current status
CURRENT_STATUS="$(tr -d ' \t\r\n' < "$STATUS_FILE" | tr '[:upper:]' '[:lower:]')"

# Normalize
case "$CURRENT_STATUS" in
  activated|active|on|1|true|yes)
    CURRENT_STATUS="activated"
    ;;
  deactivated|inactive|off|0|false|no)
    CURRENT_STATUS="deactivated"
    ;;
  *)
    echo "Invalid status in $STATUS_FILE: $CURRENT_STATUS"
    exit 2
    ;;
esac

# 4) Toggle status
if [[ "$CURRENT_STATUS" == "activated" ]]; then
  NEW_STATUS="deactivated"
else
  NEW_STATUS="activated"
fi

# 5) Write updated status EVERY run
echo "$NEW_STATUS" > "$STATUS_FILE"

# Helpers
is_running() {
  pgrep -x "$IDLE_BIN" >/dev/null 2>&1
}

stop_idle() {
  pkill -x "$IDLE_BIN" || true
}

start_idle() {
  if is_running; then
    return
  fi

  if [[ "$IDLE_BIN" == "hypridle" ]]; then
    nohup hypridle >/dev/null 2>&1 &
  else
    # Replace with your real swayidle arguments if needed
    nohup swayidle -w >/dev/null 2>&1 &
  fi
}

# 6) Apply new state
if [[ "$NEW_STATUS" == "activated" ]]; then
  start_idle
  echo "Idle manager ENABLED ($IDLE_BIN)"
else
  stop_idle
  echo "Idle manager DISABLED ($IDLE_BIN)"
fi
