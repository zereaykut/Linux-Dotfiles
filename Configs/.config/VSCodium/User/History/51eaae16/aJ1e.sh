#!/usr/bin/env bash

if pgrep -x "wl-paste" >/dev/null; then
    killall wl-paste
fi

wl-paste --watch cliphist store &
