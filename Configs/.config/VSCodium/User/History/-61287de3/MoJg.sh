#!/usr/bin/env bash

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

reset_xdg_desktop_portal_services_hyprland() {
    # Restart xdg-desktop-portal services for Hyprland, GNOME, KDE, LXQt, and Wayland.
    # Kills any running xdg-desktop-portal processes, then restarts them to reset the desktop portal services.
    lib_path=/usr/lib

    $lib_path/xdg-desktop-portal-hyprland &
    sleep 2
    $lib_path/xdg-desktop-portal &
}


kill_xdg_desktop_portal_services

reset_xdg_desktop_portal_services_hyprland

# reset_xdg_desktop_portal_services_niri