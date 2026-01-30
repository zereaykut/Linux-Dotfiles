#!/usr/bin/env bash

# This script restarts xdg-desktop-portal services. 
# It first kills any running portal backends, then starts the Hyprland-specific 
# backends (xdg-desktop-portal-hyprland and the main xdg-desktop-portal). 
# A placeholder function is included for a future Niri backend.

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


kill_xdg_desktop_portal_services

start_xdg_desktop_portal_services_hyprland

# start_xdg_desktop_portal_services_niri