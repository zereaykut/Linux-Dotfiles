#!/usr/bin/env bash

###############################################################################
# Update Script
#
# This script updates Linux systems across multiple distributions by
# automatically detecting the available package manager and running the
# appropriate update commands.
#
# Supported:
#   • Arch Linux: pacman + yay (if installed)
#   • Fedora: dnf
#   • Ubuntu/Debian: apt
#   • Flatpak: universal updates (if installed)
#
# Additional features:
#   • Triggers a Waybar module refresh on exit (ignored if Waybar isn't running)
#   • Exits on errors (set -e)
#
# Usage:
#   1. Save this script as update-system.sh
#   2. Make it executable: chmod +x update-system.sh
#   3. Run: ./update-system.sh
#
###############################################################################

set -e

# Refresh waybar on exit (Arch users)
trap 'pkill -RTMIN+20 waybar 2>/dev/null || true' EXIT

# Detect package manager
if command -v pacman &>/dev/null; then
    DISTRO="arch"
elif command -v dnf &>/dev/null; then
    DISTRO="fedora"
elif command -v apt &>/dev/null; then
    DISTRO="ubuntu-debian"
else
    echo "Unsupported distribution or package manager not found."
    exit 1
fi

echo "Detected distro: $DISTRO"
echo "Updating..."

case "$DISTRO" in
    arch)
        sudo pacman -Syu

        # Update AUR via yay if installed
        if command -v yay &>/dev/null; then
            yay -Syu
        fi
        ;;

    fedora)
        sudo dnf upgrade --refresh -y
        ;;

    ubuntu-debian)
        sudo apt update
        sudo apt full-upgrade -y
        sudo apt autoremove -y
        ;;
esac

# Flatpak updates (works on all distros)
if command -v flatpak &>/dev/null; then
    flatpak update -y
fi

echo "System update completed."
