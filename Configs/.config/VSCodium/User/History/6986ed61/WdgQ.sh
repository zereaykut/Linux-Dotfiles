#!/usr/bin/env bash

# Network manager applet
if pgrep -x "nm-applet" >/dev/null; then
    killall nm-applet
fi

nm-applet --indicator &

# Bluetooth applet
if pgrep -x "blueman-applet" >/dev/null; then
    killall blueman-applet
fi

blueman-applet &

# External drive manager
if pgrep -x "udiskie" >/dev/null; then
    killall udiskie
fi

udiskie --no-automount --smart-tray &

# KDE connect (optional)
if pgrep -x "kdeconnect-cli" >/dev/null; then
    killall kdeconnect-cli
fi

# kdeconnect-cli &
