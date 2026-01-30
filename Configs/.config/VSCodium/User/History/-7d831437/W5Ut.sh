#!/usr/bin/env bash

# Kill if running
if pgrep -x "swayosd-server" >/dev/null; then
    killall swayosd-server
fi

# Run swayosd
swayosd-server &
