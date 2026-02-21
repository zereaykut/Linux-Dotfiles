#!/usr/bin/env bash

# USAGE: ./app-launcher.sh "clipboard"
#        ./app-launcher.sh "window-management"

MODE="$1"

# NOTE: Vicinae uses "Deeplinks" to open specific extensions.
# You can find the exact link for any command by:
# 1. Opening Vicinae
# 2. Searching for the command (e.g., "Clipboard History")
# 3. Ctrl+B -> "Copy Deeplink"

case "$MODE" in
"clipboard")
    vicinae "vicinae://extensions/vicinae/clipboard/history"
    ;;

"window-management")
    vicinae "vicinae://extensions/vicinae/wm/switch-windows"
    ;;

"applications")
    vicinae toggle
    ;;

"emoji-picker")
    vicinae "vicinae://extensions/vicinae/core/search-emojis"
    ;;

"search-files")
    vicinae "vicinae://extensions/vicinae/files/search"
    ;;

*)
    echo "Unknown mode: $MODE"
    exit 1
    ;;
esac
