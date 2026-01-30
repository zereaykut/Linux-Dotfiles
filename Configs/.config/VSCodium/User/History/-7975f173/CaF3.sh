#!/usr/bin/env bash

apps_list=(
    # --- System & Hardware ---
    "wl-paste --watch cliphist store"           # Clipboard manager
    "udiskie --no-automount --smart-tray"       # External drive manager
    "swayosd-server"                            # On-screen display server (volume/brightness UI)

    # --- Connectivity ---
    "nm-applet --indicator"                     # Network manager applet
    "blueman-applet"                            # Bluetooth applet
    # "kdeconnect-cli"                          # KDE Connect (Optional)

    # --- UI & Notifications ---
    "swaync"                                    # Notification daemon
    
    # --- Maintenance ---
    # "cliphist wipe"                           # Clear clipboard on startup (Optional)
)