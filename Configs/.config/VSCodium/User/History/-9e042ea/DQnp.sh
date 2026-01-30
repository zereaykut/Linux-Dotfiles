#!/usr/bin/env bash

# Check if the file exists first
if [ -f "$HOME/.config/environment.d/custom.conf" ]; then
    # 1. Turn on 'allexport' (automatically export all defined variables)
    set -a
    
    # 2. Source the file
    source "$HOME/.config/environment.d/custom.conf"
    
    # 3. Turn off 'allexport'
    set +a
fi

# --- Ensure scripts are executable ---
chmod +x "$SOURCE_PATH/reset_xdg_portal.sh" 2>/dev/null
chmod +x "$SOURCE_PATH/theme_reload.sh" 2>/dev/null

# --- Autostart Programs & Services ---

# Reset XDPH for screen sharing
"$SOURCE_PATH/reset_xdg_portal.sh" &

# XDPH environment updates
dbus-update-activation-environment --systemd WAYLAND_DISPLAY XDG_CURRENT_DESKTOP &
dbus-update-activation-environment --systemd --all &
systemctl --user import-environment WAYLAND_DISPLAY XDG_CURRENT_DESKTOP &

# Top bas/panel (Waybar)
$SOURCE_PATH/launch_top_bar.sh

# Wallpaper daemon
swww-daemon &
swww restore &

# Clipboard manager
wl-paste --watch cliphist store &

# Notification daemon
swaync &

# Auth agent
/usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1 &

# Network manager applet
nm-applet --indicator &

# Bluetooth applet
blueman-applet &

# External drive manager
udiskie --no-automount --smart-tray &

# Idle daemon
hypridle &

# On-screen display server
swayosd-server &

# KDE connect (optional)
# kdeconnect-cli &

# Clear clipboard on startup (optional)
# cliphist wipe &

# Rebuild KDE menus
XDG_MENU_PREFIX=arch- kbuildsycoca6 &

# Theme reload script
"$SOURCE_PATH/theme_reload.sh" &

exit 0
