#!/bin/env bash
SESSION="${XDG_CURRENT_DESKTOP,,}${DESKTOP_SESSION,,}"
if [[ "$SESSION" == *"hyprland"* ]]; then
    echo "Detected Hyprland session – starting Hyprland portal services."
    waybar -c /path/to/config.jsonc.
elif [[ "$SESSION" == *"niri"* ]]; then
    echo "Detected Niri session – starting Niri portal services."
    cp -f $theme_path/niri.theme $HOME/.config/niri/modulse/theme.kdl
    niri msg reload-config
else
    echo "Unknown session ('${SESSION}') – no portal backend started."
fi
