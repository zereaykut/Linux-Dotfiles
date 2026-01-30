#!/usr/bin/env bash
set -euo pipefail

# Idle manager status file
STATUS_FILE="${XDG_CACHE_HOME:-$HOME/.cache}/idle_manager.status"

# Ensure file exists (default: activated)
mkdir -p "$(dirname "$STATUS_FILE")"
if [[ ! -f "$STATUS_FILE" ]]; then
  echo "activated" > "$STATUS_FILE"
fi

# Read + normalize status
raw_status="$(tr -d ' \t\r\n' < "$STATUS_FILE" | tr '[:upper:]' '[:lower:]')"
case "$raw_status" in
  activated|active|on|1|true|yes) status="activated" ;;
  deactivated|inactive|off|0|false|no) status="deactivated" ;;
  *) status="unknown" ;;
esac

case "$status" in
  "activated")
    text="󰅶"
    tooltip="⏲ Idle Manager: Activated"
    echo "{\"text\":\"$text\", \"tooltip\":\"$tooltip\"}"
    ;;
  "deactivated")
    text=""
    tooltip=" Idle Manager: Deactivated"
    echo "{\"text\":\"$text\", \"tooltip\":\"$tooltip\"}"
    ;;
  *)
    text=""
    tooltip=" Idle Manager: Unknown (check $STATUS_FILE)"
    echo "{\"text\":\"$text\", \"tooltip\":\"$tooltip\"}"
    ;;
esac
