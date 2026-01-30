#!/usr/bin/env bash

# --- Variables ---
source $HOME/.config/local/share/bin/global.sh
export PATH="$PATH:$SOURCE_PATH"

# --- Ensure scripts are executable ---
chmod +x "$SOURCE_PATH/reset-xdg-portal.sh" 2>/dev/null
chmod +x "$SOURCE_PATH/theme-reload.sh" 2>/dev/null

# System
reset-xdg-portal.sh
xdph-environment-updates.sh
start-top-bar.sh
start-wallpaper-daemon.sh
start-clipboard-manager.sh
start-notification-daemon.sh
start-network-manager-applet.sh

# Auth agent
/usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1 &


# Bluetooth applet
$SOURCE_PATH/start_app.sh "blueman-applet"

# External drive manager
$SOURCE_PATH/start_app.sh "udiskie --no-automount --smart-tray"

# Idle daemon
if [[ ! -f "$CACHE_PATH/idle_manager.status" ]]; then
    echo "activated" >"$CACHE_PATH/idle_manager.status"
fi
IDLE_STATUS="$(tr -d '\n\r ' <"$CACHE_PATH/idle_manager.status")"
$SOURCE_PATH/idle_manager.sh $IDLE_STATUS

# On-screen display server
$SOURCE_PATH/start_app.sh "swayosd-server"

# KDE connect (optional)
# $SOURCE_PATH/start_app.sh "kdeconnect-cli"

# Clear clipboard on startup (optional)
# $SOURCE_PATH/start_app.sh "cliphist wipe"

# Rebuild KDE menus
XDG_MENU_PREFIX=arch- kbuildsycoca6 &

# Theme reload script
$SOURCE_PATH/theme_reload.sh

exit 0
