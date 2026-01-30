#!/usr/bin/env bash

# --- Variables ---
SOURCE_PATH="$HOME/.local/share/bin"
CACHE_PATH="$HOME/.cache"

export $SOURCE_PATH
export PATH="$PATH:$SOURCE_PATH"

# --- Ensure scripts are executable ---
chmod +x "$SOURCE_PATH/reset_xdg_portal.sh" 2>/dev/null
chmod +x "$SOURCE_PATH/theme_reload.sh" 2>/dev/null

# --- Autostart Programs & Services ---

# Reset XDPH for screen sharing
$SOURCE_PATH/reset_xdg_portal.sh

# XDPH environment updates
dbus-update-activation-environment --systemd WAYLAND_DISPLAY XDG_CURRENT_DESKTOP &
dbus-update-activation-environment --systemd --all &
systemctl --user import-environment WAYLAND_DISPLAY XDG_CURRENT_DESKTOP &

# Top bas/panel (Waybar)
$SOURCE_PATH/launch_top_bar.sh

# Wallpaper daemon
$SOURCE_PATH/launch_wallpaper_daemon.sh

# Clipboard manager
wl-paste --watch cliphist store &

# Notification daemon
$SOURCE_PATH/launch_notification_daemon.sh

# Auth agent
/usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1 &

# Network manager applet
$SOURCE_PATH/start_app.sh "nm-applet --indicator"

# Bluetooth applet
blueman-applet &

# External drive manager
udiskie --no-automount --smart-tray &

# Idle daemon
if [[ ! -f "$CACHE_PATH/idle_manager.status" ]]; then
    echo "activated" >"$CACHE_PATH/idle_manager.status"
fi
IDLE_STATUS="$(tr -d '\n\r ' <"$CACHE_PATH/idle_manager.status")"
$SOURCE_PATH/idle_manager.sh $IDLE_STATUS

# On-screen display server
$SOURCE_PATH/launch_osd.sh

# KDE connect (optional)
# kdeconnect-cli &

# Clear clipboard on startup (optional)
# cliphist wipe &

# Rebuild KDE menus
XDG_MENU_PREFIX=arch- kbuildsycoca6 &

# Theme reload script
$SOURCE_PATH/theme_reload.sh

exit 0
