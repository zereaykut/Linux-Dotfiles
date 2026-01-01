#!/usr/bin/env bash

if pgrep -x "swayosd-server" >/dev/null; then
    killall swayosd-server
fi

swayosd-server &
