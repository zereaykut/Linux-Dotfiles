#!/usr/bin/env bash
set -e

SCRIPT_DIR=$(dirname "$(realpath "$0")")
LOGFILE="$SCRIPT_DIR/install.log"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S')  $*" | tee -a "$LOGFILE"
}
