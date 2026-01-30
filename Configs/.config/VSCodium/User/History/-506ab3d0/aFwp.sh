#!/usr/bin/env bash
set -e

# Load package list
source ./Packages/arch_pacman.sh
source ./Packages/arch_aur.sh
source ./Packages/flatpak.sh


# ARCH PACMAN
# Filter out installed packages
for pkg in "${PACKAGES_PACMAN[@]}"; do
    if pacman -Qi "$pkg" &>/dev/null; then
        echo "✔ $pkg already installed"
    else
        echo "➤ installing $pkg"
        sudo pacman --needed --noconfirm -S $pkg
    fi
done

# ARCH AUR with YAY
# Filter out installed packages
for pkg in "${PACKAGES_AUR[@]}"; do
    if pacman -Qi "$pkg" &>/dev/null; then
        echo "✔ $pkg already installed"
    else
        echo "➤ installing $pkg"
        yay --needed --noconfirm -S $pkg
    fi
done

echo "🎉 Installation script is completed!"