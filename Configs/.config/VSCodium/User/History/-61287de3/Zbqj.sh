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

start_xdg_desktop_portal_services_hyprland() {
    lib_path=/usr/lib

    $lib_path/xdg-desktop-portal-hyprland &
    sleep 2
    $lib_path/xdg-desktop-portal &
}




kill_xdg_desktop_portal_services

start_xdg_desktop_portal_services_hyprland

# start_xdg_desktop_portal_services_niri