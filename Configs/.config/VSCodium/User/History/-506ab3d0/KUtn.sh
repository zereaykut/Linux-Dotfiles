#!/usr/bin/env bash
set -e

# Load package list
source ./Packages/arch_pacman.sh
source ./Packages/arch_yay.sh

# Filter out installed packages
for pkg in "${PACKAGES_PACMAN[@]}"; do
    if pacman -Qi "$pkg" &>/dev/null; then
        echo "✔ $pkg already installed"
    else
        echo "➤ installing $pkg"
        sudo pacman --needed --noconfirm -S $pkg
    fi
done

echo "🎉 Installation script is completed!"