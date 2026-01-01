#!/usr/bin/env bash

SCRIPT_DIR="$(dirname "$(realpath "$0")")"
source "$SCRIPT_DIR/global_fn.sh"

# ========================================================== >> ARCH PACMAN
install_arch_pacman_packages() {
    source "$SCRIPT_DIR/Packages/arch_pacman.sh"

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


# ========================================================== >> ARCH AUR (YAY)
install_arch_aur_packages() {
    source "$SCRIPT_DIR/Packages/arch_aur.sh"

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

# ========================================================== >> FEDORA DNF
install_fedora_dnf_packages() {
    source "$SCRIPT_DIR/Packages/fedora_dnf.sh"

    log "=== Starting DNF package installation ==="

    for pkg in "${PACKAGES_DNF[@]}"; do
        if rpm -q "$pkg" &>/dev/null; then
            log "✔ $pkg already installed"
        else
            log "➤ installing $pkg"
            sudo dnf install -y "$pkg"
        fi
    done

    log "=== Finished DNF packages ==="
}

# ========================================================== >> FEDORA COPR
install_fedora_copr_packages() {
    source "$SCRIPT_DIR/Packages/fedora_copr.sh"

    log "=== Starting COPR repository installation ==="

    for repo in "${PACKAGES_COPR[@]}"; do
        log "➤ enabling COPR $repo"
        sudo dnf copr enable -y "$repo"
    done

    log "=== Installing packages from COPR / RPM Fusion ==="

    for pkg in "${PACKAGES_RPMFUSION[@]}"; do
        if rpm -q "$pkg" &>/dev/null; then
            log "✔ $pkg already installed"
        else
            log "➤ installing $pkg"
            sudo dnf install -y "$pkg"
        fi
    done

    log "=== Finished COPR packages ==="
}

# ========================================================== >> UBUNTU APT
install_ubuntu_apt_packages() {
    source "$SCRIPT_DIR/Packages/ubuntu_apt.sh"

    log "=== Updating APT ==="
    sudo apt update -y

    log "=== Installing APT packages ==="
    for pkg in "${PACKAGES_APT[@]}"; do
        if dpkg -l | grep -q "^ii  $pkg "; then
            log "✔ $pkg already installed"
        else
            log "➤ installing $pkg"
            sudo apt install -y "$pkg"
        fi
    done
}


# ========================================================== >> UBUNTU PPA
install_ubuntu_ppa_repos() {
    source "$SCRIPT_DIR/Packages/ubuntu_ppa.sh"

    log "=== Adding PPAs ==="

    for ppa in "${PPAS[@]}"; do
        log "➤ Adding $ppa"
        sudo add-apt-repository -y "$ppa"
    done

    sudo apt update -y
}

# ========================================================== >> FLATPAK
install_flatpak_apps() {
    source "$SCRIPT_DIR/Packages/flatpak.sh"

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
