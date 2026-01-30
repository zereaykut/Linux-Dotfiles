#!/bin/env bash
SESSION="${XDG_CURRENT_DESKTOP,,}${DESKTOP_SESSION,,}"
if [[ "$SESSION" == *"hyprland"* ]]; then
    echo "Detected Hyprland session"
    waybar -c ~/.config/waybar/config_hyprland.jsonc
elif [[ "$SESSION" == *"niri"* ]]; then
    echo "Detected Niri session"
    cp -f $theme_path/niri.theme $HOME/.config/niri/modulse/theme.kdl
    niri msg reload-config
else
    echo "Unknown session ('${SESSION}') – no portal backend started."
fi
