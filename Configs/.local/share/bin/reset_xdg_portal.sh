#!/usr/bin/env bash

# This script restarts xdg-desktop-portal services.
# It first kills any running portal backends, then starts the correct backend
# depending on the active session (Hyprland or Niri).

LIB_PATH=/usr/lib

kill_xdg_desktop_portal_services() {
    sleep 1
    killall xdg-desktop-portal-hyprland
    killall xdg-desktop-portal-gnome
    killall xdg-desktop-portal-kde
    killall xdg-desktop-portal-lxqt
    killall xdg-desktop-portal-wlr
    killall xdg-desktop-portal
    sleep 1
}

start_xdg_desktop_portal_services_hyprland() {
    $LIB_PATH/xdg-desktop-portal-hyprland &
    sleep 2
    $LIB_PATH/xdg-desktop-portal &
}

start_xdg_desktop_portal_services_niri() {
    $LIB_PATH/xdg-desktop-portal-wlr &
    sleep 2
    $LIB_PATH/xdg-desktop-portal &
}


# Detect session
SESSION="${XDG_CURRENT_DESKTOP,,}${DESKTOP_SESSION,,}"

kill_xdg_desktop_portal_services

if [[ "$SESSION" == *"hyprland"* ]]; then
    echo "Detected Hyprland session – starting Hyprland portal services."
    start_xdg_desktop_portal_services_hyprland
elif [[ "$SESSION" == *"niri"* ]]; then
    echo "Detected Niri session – starting Niri portal services."
    start_xdg_desktop_portal_services_niri
else
    echo "Unknown session ('${SESSION}') – no portal backend started."
fi