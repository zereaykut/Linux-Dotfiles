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
#   - Falls back to checking running processes (hyprland / niri / wayfire)
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
#   • Wayfire:
#       - Lists all toplevel windows via `wlrctl toplevel list`
#       - Extracts each window ID and closes them using:
#           wlrctl toplevel close <id>
#
# Requirements:
#   - jq must be installed
#   - Hyprland, Niri or Wayfire must be running
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
    elif pgrep -x wayfire >/dev/null; then
        SESSION="wayfire"
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

###########################################
# Wayfire
###########################################
if [[ "$SESSION" == *"wayfire"* ]]; then
    echo "Closing all windows in Wayfire..."

    # Check for wlrctl
    if ! command -v wlrctl >/dev/null; then
        echo "Error: wlrctl is required for Wayfire window control but was not found."
        echo "Install wf-utils or wlrctl."
        exit 1
    fi

    # List all toplevel IDs and close them
    wlrctl toplevel list | grep "ID:" | awk '{print $2}' | while read -r id; do
        wlrctl toplevel close "$id"
    done

    echo "All Wayfire windows closed."
    exit 0
fi

echo "Unsupported or unknown SESSION. (Supported: Hyprland, Niri Wayfire)"
exit 1
