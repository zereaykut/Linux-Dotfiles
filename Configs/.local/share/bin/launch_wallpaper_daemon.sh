#!/usr/bin/env bash

if pgrep -x "swww-daemon" >/dev/null; then
    killall swww-daemon
fi

swww-daemon &
swww restore &
