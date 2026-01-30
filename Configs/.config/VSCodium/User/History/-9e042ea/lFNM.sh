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
start-osd.sh
start-authentication-agent.sh

# Applets
start-bluetooth-applet.sh
start-external-drive-manager.sh
start-network-manager-applet.sh

# Idle daemon
if [[ ! -f "$CACHE_PATH/idle_manager.status" ]]; then
    echo "activated" >"$CACHE_PATH/idle_manager.status"
fi
IDLE_STATUS="$(tr -d '\n\r ' <"$CACHE_PATH/idle_manager.status")"
$SOURCE_PATH/idle_manager.sh $IDLE_STATUS


# KDE connect (optional)
# $SOURCE_PATH/start_app.sh "kdeconnect-cli"

# Clear clipboard on startup (optional)
# $SOURCE_PATH/start_app.sh "cliphist wipe"

# Rebuild KDE menus
XDG_MENU_PREFIX=arch- kbuildsycoca6 &

# Theme reload script
$SOURCE_PATH/theme-reload.sh

exit 0
