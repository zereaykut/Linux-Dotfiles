#!/usr/bin/env bash

SOURCE_DIR="$(dirname "$(realpath "$0")")"

LOGFILE="$SOURCE_DIR/install.log"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S')  $*" | tee -a "$LOGFILE"
}

echo $scrDir