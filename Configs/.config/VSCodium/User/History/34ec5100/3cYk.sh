#!/usr/bin/env bash

SESSION="${XDG_CURRENT_DESKTOP,,}${DESKTOP_SESSION,,}"

# Select correct config depending on session
if [[ "$SESSION" == *"hyprland"* ]]; then
    CONFIG="$HOME/.config/waybar/config_hyprland.jsonc"
elif [[ "$SESSION" == *"niri"* ]]; then
    CONFIG="$HOME/.config/waybar/config_niri.jsonc"
else
    echo "Unknown session ('${SESSION}') – no portal backend started."
    exit 1
fi

# 1–3: Kill if running, otherwise start
if pgrep -x "waybar" >/dev/null; then
    killall waybar
fi

waybar -c "$CONFIG" &
