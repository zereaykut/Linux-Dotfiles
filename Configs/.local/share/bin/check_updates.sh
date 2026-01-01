#!/usr/bin/env bash

# Detect distribution
get_distro() {
    if command -v pacman >/dev/null 2>&1; then
        echo "arch"
    elif command -v dnf >/dev/null 2>&1; then
        echo "fedora"
    elif command -v apt >/dev/null 2>&1; then
        echo "ubuntu"
    else
        echo "unknown"
    fi
}

DISTRO=$(get_distro)

############################################################
# Update check functions for each distro
############################################################

check_arch() {
    pacman_updates=$(checkupdates 2>/dev/null | wc -l)

    if command -v yay >/dev/null 2>&1; then
        yay_updates=$(yay -Qum 2>/dev/null | wc -l)
    else
        yay_updates=0
    fi

    echo "$pacman_updates" "$yay_updates"
}

check_fedora() {
    # dnf updateinfo may require metadata refresh
    dnf_updates=$(dnf updateinfo list updates 2>/dev/null | grep -cE "Important|Update" || true)
    echo "$dnf_updates"
}

check_ubuntu() {
    apt_updates=$(apt list --upgradable 2>/dev/null | grep -vc "Listing" || true)
    echo "$apt_updates"
}

# Flatpak is available on all distros if installed
check_flatpak() {
    if command -v flatpak >/dev/null 2>&1; then
        flatpak remote-ls --updates 2>/dev/null | wc -l
    else
        echo 0
    fi
}

############################################################
# Compute update counts
############################################################

case "$DISTRO" in
    arch)
        read pacman_updates yay_updates < <(check_arch)
        flatpak_updates=$(check_flatpak)
        updates=$((pacman_updates + yay_updates + flatpak_updates))
        tooltip="󰮯 pacman $pacman_updates\n yay $yay_updates\n flatpak $flatpak_updates"
        ;;
    fedora)
        dnf_updates=$(check_fedora)
        flatpak_updates=$(check_flatpak)
        updates=$((dnf_updates + flatpak_updates))
        tooltip="󰮯 dnf $dnf_updates\n flatpak $flatpak_updates"
        ;;
    ubuntu)
        apt_updates=$(check_ubuntu)
        flatpak_updates=$(check_flatpak)
        updates=$((apt_updates + flatpak_updates))
        tooltip="󰮯 apt $apt_updates\n flatpak $flatpak_updates"
        ;;
    *)
        echo "{\"text\":\"󰮯 ?\", \"tooltip\":\"Unsupported distribution\"}"
        exit 0
        ;;
esac

############################################################
# Output for Waybar
############################################################

if [ "$updates" -eq 0 ]; then
    echo "{\"text\":\"󰮯\", \"tooltip\":\" Packages are up to date\"}"
else
    echo "{\"text\":\"󰮯 $updates\", \"tooltip\":\"$tooltip\"}"
fi
