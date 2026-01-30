#!/usr/bin/env bash

source $HOME/.config/local/share/bin/global.sh
export PATH="$PATH:$SOURCE_PATH"

# chmod +x "$SOURCE_PATH/reset-xdg-portal.sh" 2>/dev/null
# chmod +x "$SOURCE_PATH/theme-reload.sh" 2>/dev/null

# System
reset-xdg-portal.sh
xdph-environment-updates.sh
start-wallpaper-daemon.sh
start-clipboard-manager.sh
start-authentication-agent.sh

# These are run at theme-switcher.sh in theme-reload.sh
# start-top-bar.sh
# start-notification-daemon.sh
# start-osd.sh

# Applets
start-bluetooth-applet.sh
start-external-drive-manager.sh
start-network-manager-applet.sh

# Idle daemon
if [[ ! -f "$CACHE_PATH/idle_manager.status" ]]; then
    echo "activated" >"$CACHE_PATH/idle_manager.status"
fi
IDLE_STATUS="$(tr -d '\n\r ' <"$CACHE_PATH/idle_manager.status")"
idle-manager.sh $IDLE_STATUS


# KDE connect (optional)
# $SOURCE_PATH/start_app.sh "kdeconnect-cli"

# Clear clipboard on startup (optional)
# $SOURCE_PATH/start_app.sh "cliphist wipe"

# Rebuild KDE menus
XDG_MENU_PREFIX=arch- kbuildsycoca6 &

# Theme reload script
theme-reload.sh

exit 0
