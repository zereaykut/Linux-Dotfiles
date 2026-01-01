#!/usr/bin/env bash

if pgrep -x "swaync" >/dev/null; then
    killall swaync
fi

swaync &
