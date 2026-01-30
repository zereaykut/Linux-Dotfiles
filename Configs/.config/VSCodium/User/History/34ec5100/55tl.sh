#!/bin/env bash
SESSION="${XDG_CURRENT_DESKTOP,,}${DESKTOP_SESSION,,}"
if [[ "$SESSION" == *"hyprland"* ]]; then
    echo "Detected Hyprland session"
    killall waybar || waybar -c ~/.config/waybar/config_hyprland.jsonc &
elif [[ "$SESSION" == *"niri"* ]]; then
    echo "Detected Niri session"
    killall waybar || waybar -c ~/.config/waybar/config_niri.jsonc &
else
    echo "Unknown session ('${SESSION}') – no portal backend started."
fi
