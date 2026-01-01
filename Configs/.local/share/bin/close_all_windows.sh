#!/usr/bin/env bash

###############################################################
# close_all_windows.sh
#
# This script detects whether the current Wayland SESSION is
# running under Hyprland or Niri window manager, and then
# automatically closes all open windows in that SESSION.
#
# Detection:
#   - Uses $XDG_CURRENT_DESKTOP when available
#   - Falls back to checking running processes (hyprland / niri)
#
# Actions:
#   • Hyprland:
#       - Lists all clients via `hyprctl clients -j`
#       - Extracts each window address and closes them using:
#           hyprctl dispatch closewindow <addr>
#
#   • Niri:
#       - Lists windows via `niri msg -j windows`
#       - Extracts window IDs and closes them using:
#           niri msg action close-window <id>
#
#
# Requirements:
#   - jq must be installed
#   - Hyprland or Niri must be running
#
# Usage:
#   chmod +x close_all_windows.sh
#   ./close_all_windows.sh
###############################################################

# Detect current Wayland compositor based on XDG_CURRENT_DESKTOP or WAYLAND_DISPLAY
SESSION="${XDG_CURRENT_DESKTOP,,}${DESKTOP_SESSION,,}"

# Fallback: query running processes if the variable is empty
if [[ -z "$SESSION" ]]; then
    if pgrep -x hyprland >/dev/null; then
        SESSION="hyprland"
    elif pgrep -x niri >/dev/null; then
        SESSION="niri"
    fi
fi

echo "Detected SESSION: $SESSION"

###########################################
# Hyprland
###########################################
if [[ "$SESSION" == *"hyprland"* ]]; then
    echo "Closing all windows in Hyprland..."

    # hyprctl clients -j | jq -r '.[].address' | while read -r addr; do
    #     hyprctl dispatch closewindow "$addr"
    # done

    hyprctl clients -j | \
        jq -r ".[].address" | \
        xargs -I{} hyprctl dispatch closewindow address:{}

    # Move to first workspace
    hyprctl dispatch workspace 1

    exit 0
fi


###########################################
# Niri
###########################################
if [[ "$SESSION" == *"niri"* ]]; then
    echo "Closing all windows in Niri..."

    niri msg -j windows | jq -r '.[].id' | while read -r wid; do
        niri msg action close-window --id "$wid"
    done

    # niri msg -j windows | \
    #     jq -r '.[].node_id' | \
    #     xargs -I{} niri msg action close-window --id {}

    niri msg action focus-workspace 1

    exit 0
fi


echo "Unsupported or unknown SESSION. (Supported: Hyprland, Niri)"
exit 1
