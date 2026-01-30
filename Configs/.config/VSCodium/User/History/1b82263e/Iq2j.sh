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

install_arch_pacman_packages
install_arch_aur_packages
install_flatpak_apps

log "🎉 Package installation completed!"

# ========================================================== >> Config Setup

source "$SCRIPT_DIR/config_setup_folders.sh"

create_folders
copy_configs
setup_sddm
setup_cursor
setup_grub
setup_resolved
setup_zapret

log "🎉 Folder and config setup completed!"

# ========================================================== >> Systemctl & Setups

source "$SCRIPT_DIR/systemctl_setups.sh"

enable_services
setup_flatpak_overrides
setup_user_groups
setup_resolved
setup_zapret
setup_shell
setup_hyprland_plugins

log "🎉 System services and plugins setup completed!"

# ========================================================== >> Themes & Icons & Cursors

source "$SCRIPT_DIR/themes_icons_cursors.sh"

install_gtk_themes
install_icons
install_cursors

log "🎉 Themes, icons, and cursors installation completed!"