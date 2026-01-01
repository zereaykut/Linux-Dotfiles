#!/usr/bin/env bash

SCRIPT_DIR="$(dirname "$(realpath "$0")")"
source "$SCRIPT_DIR/global_fn.sh"

# ========================================================== >> Enable Systemd Services
enable_services() {
    log "=== Enabling systemd services ==="
    
    sudo systemctl enable sddm                       # login manager
    sudo systemctl enable bluetooth                  # bluetooth
    systemctl enable --user pipewire-pulse.service  # user audio
    sudo systemctl enable --now swayosd-libinput-backend.service
    sudo systemctl enable firewalld.service         # firewall

    log "Systemd services enabled"
}

# ========================================================== >> Flatpak Overrides
setup_flatpak_overrides() {
    log "=== Setting up Flatpak overrides ==="

    sudo flatpak override --filesystem=$HOME/.themes
    sudo flatpak override --filesystem=$HOME/.icons

    log "Flatpak overrides applied"
}

# ========================================================== >> User Groups
setup_user_groups() {
    log "=== Adding user to groups ==="

    sudo usermod -aG input "$(whoami)"   # waybar keyboard-state widget
    sudo usermod -aG video "$(whoami)"   # video permissions

    log "User added to input and video groups"
}

# ========================================================== >> DNS (systemd-resolved)
setup_resolved() {
    log "=== Enabling systemd-resolved ==="

    sudo systemctl enable systemd-resolved
    sudo systemctl start systemd-resolved

    log "systemd-resolved enabled and started"
}

# ========================================================== >> Zapret
setup_zapret() {
    log "=== Enabling Zapret ==="

    sudo systemctl enable zapret
    sudo systemctl start zapret

    log "Zapret enabled and started"
}

# ========================================================== >> Change Default Shell
setup_shell() {
    log "=== Changing default shell to Fish ==="

    chsh -s "$(which fish)"

    log "Default shell set to Fish"
}

# ========================================================== >> Hyprland Plugins
setup_hyprland_plugins() {
    log "=== Setting up Hyprland plugins ==="

    hyprpm update
    hyprpm add https://github.com/hyprwm/hyprland-plugins
    hyprpm enable hyprexpo

    log "Hyprland plugins configured"
}