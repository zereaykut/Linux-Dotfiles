#!/usr/bin/env bash

# 1. Get the application name from the first argument
APP="$1"

# 2. Check if an argument was actually provided
if [ -z "$APP" ]; then
    notify-send "System Error" "No application name provided to the toggle script."
    exit 1
fi

# 3. Check if the application exists (is installed/executable)
if ! command -v "$APP" >/dev/null 2>&1; then
    notify-send "System Error" "Application '$APP' not found or not executable."
    exit 1
fi

# 4. Toggle Logic
# Check if the process is running exactly matches the name (-x)
if pgrep -x "$APP" >/dev/null; then
    # If running, kill it
    killall "$APP"
else
    # If not running, start it in the background
    "$APP" &
fi