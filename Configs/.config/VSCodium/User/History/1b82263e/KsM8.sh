#!/usr/bin/env bash

SOURCE_DIR="$(dirname "$(realpath "$0")")"
LOGFILE="$SOURCE_DIR/install.log"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S')  $*" | tee -a "$LOGFILE"
}

# ========================================================== >> Packages

source ./packages.sh

install_pacman_packages
install_aur_packages
install_flatpak_apps

log "🎉 Package installation completed!"