#!/usr/bin/env bash

# 1. Capture the full command string (First Argument)
FULL_CMD="$1"

# 2. Capture the toggle mode (Second Argument)
#    Defaults to "false" if not provided.
#    true  = Toggle Mode (If running -> Stop. If stopped -> Start)
#    false = Restart Mode (If running -> Restart. If stopped -> Start)
TOGGLE="${2:-false}"

# 3. Extract just the binary name (everything before the first space)
BIN="${FULL_CMD%% *}"

# 4. Check if an application name was provided
if [ -z "$FULL_CMD" ]; then
    notify-send "System Error" "No application name provided." -u critical
    exit 1
fi

# 5. Check if the binary exists
if ! command -v "$BIN" >/dev/null 2>&1; then
    notify-send "System Error" "Application '$BIN' not found." -u critical
    exit 1
fi

# 6. Toggle/Restart Logic
if pgrep -x "$BIN" >/dev/null; then
    # --- App is RUNNING ---
    killall "$BIN"
    
    # If TOGGLE is false, we want to RESTART (Kill -> Run)
    if [ "$TOGGLE" = "false" ]; then
        # Wait a tiny bit to ensure the old process closes
        sleep 0.2
        $FULL_CMD &
    fi
    # If TOGGLE is true, we stop here (Kill -> Stop)

else
    # --- App is NOT RUNNING ---
    # Start it regardless of the mode
    $FULL_CMD &
fi