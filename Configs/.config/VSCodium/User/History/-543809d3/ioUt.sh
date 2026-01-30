#!/usr/bin/env bash
SESSION="${XDG_CURRENT_DESKTOP,,}${DESKTOP_SESSION,,}"

echo $SESSION

if [[ "$SESSION" == *"hyprland"* ]]; then
    echo "Detected Hyprland session – starting Hyprland portal services."
elif [[ "$SESSION" == *"niri"* ]]; then
    echo "Detected Niri session – starting Niri portal services."
else
    echo "Unknown session ('${SESSION}') – no portal backend started."
fi