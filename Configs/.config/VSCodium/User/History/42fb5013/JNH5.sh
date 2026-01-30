#!/usr/bin/env bash

# 1. Capture the full command string passed as an argument
FULL_CMD="$1"

# 2. Extract just the binary name (everything before the first space)
#    If there are no spaces, BIN becomes the same as FULL_CMD
BIN="${FULL_CMD%% *}"

# 3. Check if an argument was provided
if [ -z "$FULL_CMD" ]; then
    notify-send "System Error" "No application name provided." -u critical
    exit 1
fi

# 4. Check if the binary exists
if ! command -v "$BIN" >/dev/null 2>&1; then
    notify-send "System Error" "Application '$BIN' not found." -u critical
    exit 1
fi

# 5. Toggle Logic
# We check pgrep using ONLY the binary name ($BIN)
if pgrep -x "$BIN" >/dev/null; then
    # Kill the process by name
    killall "$BIN"
    $FULL_CMD &
else
    # Launch using the FULL command string (with arguments)
    # Use 'setsid' or just '&' to detach it from the shell
    $FULL_CMD &
fi