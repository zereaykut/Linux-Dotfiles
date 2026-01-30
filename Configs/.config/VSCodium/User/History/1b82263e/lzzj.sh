#!/usr/bin/env bash

# ========================================================== >> MAIN EXECUTION

install_pacman_packages
install_aur_packages
install_flatpak_apps

log "🎉 Package installation completed!"