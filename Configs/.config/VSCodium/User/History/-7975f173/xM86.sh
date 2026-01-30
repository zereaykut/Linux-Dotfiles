#!/usr/bin/env bash

apps_list=(
    # --- System Indicators ---
    "swaync"                 # Notification Center
    "nm-applet --indicator"  # Network Manager (needs the flag for tray icon)
    "blueman-applet"         # Bluetooth

    # --- Desktop UI ---
    "waybar"
    
    # "discord"              # Commented out: Don't start Discord automatically right now
    # "spotify" 
)