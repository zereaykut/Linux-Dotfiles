#!/usr/bin/env bash

LOGFILE="install.log"

scrDir="$(dirname "$(realpath "$0")")"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S')  $*" | tee -a "$LOGFILE"
}