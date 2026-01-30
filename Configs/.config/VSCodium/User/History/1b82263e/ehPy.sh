#!/usr/bin/env bash

SCRIPT_DIR="$(dirname "$(realpath "$0")")"
source "$SCRIPT_DIR/global_fn.sh"

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

# ========================================================== >> Config Setup

source "$SCRIPT_DIR/packages.sh"

create_folders
copy_configs
setup_sddm
setup_cursor
setup_grub
setup_resolved
setup_zapret

log "🎉 Folder and config setup completed!"