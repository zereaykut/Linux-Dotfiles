#!/usr/bin/env bash

# ========================================================== >> MAIN EXECUTION

source ./packages.sh

install_pacman_packages
install_aur_packages
install_flatpak_apps

log "🎉 Package installation completed!" >> 