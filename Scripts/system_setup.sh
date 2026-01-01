#!/usr/bin/env bash

SCRIPT_DIR="$(dirname "$(realpath "$0")")"
source "$SCRIPT_DIR/global_fn.sh"

# ========================================================== >> Pacman config
setup_pacman_conf() {
    log "=== Updating pacman.conf ==="
    
    sudo cp "$SCRIPT_DIR/../Move/pacman/pacman.conf" /etc/pacman.conf

    log "Pacman config updated"
}

# ========================================================== >> Chaotic AUR repo
setup_chaotic_aur() {
    log "=== Setting up Chaotic AUR ==="

    # Retrieve and sign keys
    log "Adding Chaotic AUR keys..."
    sudo pacman-key --recv-key 3056513887B78AEB --keyserver keyserver.ubuntu.com
    sudo pacman-key --lsign-key 3056513887B78AEB

    # Install keyring + mirrorlist
    log "Installing chaotic-keyring and chaotic-mirrorlist..."
    sudo pacman --needed --noconfirm -U 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-keyring.pkg.tar.zst'
    sudo pacman --needed --noconfirm -U 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-mirrorlist.pkg.tar.zst'

    # Replace pacman.conf
    log "Copying pacman.conf with Chaotic AUR enabled..."
    sudo cp "$SCRIPT_DIR/../Move/pacman/pacman_chaotic_aur.conf" /etc/pacman.conf

    log "Running full system update..."
    sudo pacman --needed --noconfirm -Syu

    log "Chaotic AUR setup completed"
}

# ========================================================== >> Install yay
install_yay() {
    log "=== Installing yay AUR helper ==="

    sudo pacman --needed --noconfirm -S git base-devel

    git clone https://aur.archlinux.org/yay.git
    cd yay

    makepkg -si

    cd ..
    rm -rf yay

    log "yay installed successfully"
}
