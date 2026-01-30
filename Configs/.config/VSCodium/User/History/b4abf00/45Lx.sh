#!/usr/bin/env bash
set -e

source ./global_fn.sh

# ========================================================== >> PACMAN
install_pacman_packages() {
    source ./Packages/arch_pacman.sh

    log "=== Starting PACMAN package installation ==="

    for pkg in "${PACKAGES_PACMAN[@]}"; do
        if pacman -Qi "$pkg" &>/dev/null; then
            log "✔ $pkg already installed"
        else
            log "➤ installing $pkg"
            sudo pacman --needed --noconfirm -S "$pkg"
        fi
    done

    log "=== Finished PACMAN packages ==="
}


# ========================================================== >> AUR (YAY)
install_aur_packages() {
    source ./Packages/arch_aur.sh

    log "=== Starting AUR package installation ==="

    for pkg in "${PACKAGES_AUR[@]}"; do
        if pacman -Qi "$pkg" &>/dev/null; then
            log "✔ $pkg already installed"
        else
            log "➤ installing $pkg"
            yay --needed --noconfirm -S "$pkg"
        fi
    done

    log "=== Finished AUR packages ==="
}


# ========================================================== >> FLATPAK
install_flatpak_apps() {
    source ./Packages/flatpak.sh

    log "=== Starting Flatpak installation ==="

    for app in "${FLATPAK_APPS[@]}"; do
        if flatpak list --app --columns=application | grep -q "^${app}$"; then
            log "✔ $app already installed"
        else
            log "➤ installing $app"
            flatpak install -y --noninteractive flathub "$app"
        fi
    done

    log "=== Finished Flatpak apps ==="
}
