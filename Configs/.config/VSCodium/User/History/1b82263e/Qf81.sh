#!/usr/bin/env bash

SCRIPT_DIR="$(dirname "$(realpath "$0")")"
LOGFILE="$SCRIPT_DIR/install.log"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S')  $*" | tee -a "$LOGFILE"
}

# ========================================================== >> System Setup
source "$SCRIPT_DIR/system_setup.sh"

setup_pacman_conf
setup_chaotic_aur
install_yay

log "🎉 System setup completed!"

# ========================================================== >> Packages

source "$SCRIPT_DIR/packages.sh"

install_pacman_packages
install_aur_packages
install_flatpak_apps

log "🎉 Package installation completed!"