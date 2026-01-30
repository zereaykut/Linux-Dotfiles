#!/usr/bin/env bash

# --- Configuration ---
# true  = If app is running, kill it (Stop/Toggle Off)
# false = If app is running, kill it and start again (Restart/Reload)
TOGGLE=${TOGGLE:-false}

# 1. Capture the full command string passed as an argument
FULL_CMD="$1"

# 2. Extract just the binary name (everything before the first space)
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

# 5. Toggle/Restart Logic
if pgrep -x "$BIN" >/dev/null; then
    # --- App is RUNNING ---
    killall "$BIN"
    
    # If TOGGLE is false, we strictly want to RESTART (Kill -> Run)
    if [ "$TOGGLE" = "false" ]; then
        # Wait a tiny bit to ensure process handles are released
        sleep 0.2
        $FULL_CMD &
    fi
    # If TOGGLE is true, we do nothing else (Kill -> Stop)

else
    # --- App is NOT RUNNING ---
    # Start it regardless of the TOGGLE setting
    $FULL_CMD &
fi