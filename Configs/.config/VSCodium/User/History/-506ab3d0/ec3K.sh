#!/usr/bin/env bash
set -e

# ARCH PACMAN
source ./Packages/arch_pacman.sh

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
source ./Packages/arch_aur.sh

# Filter out installed packages
for pkg in "${PACKAGES_AUR[@]}"; do
    if pacman -Qi "$pkg" &>/dev/null; then
        echo "✔ $pkg already installed"
    else
        echo "➤ installing $pkg"
        yay --needed --noconfirm -S $pkg
    fi
done


# FLATPAK
source ./Packages/flatpak.sh

# Check each app
for app in "${FLATPAK_APPS[@]}"; do
    if flatpak list --app --columns=application | grep -q "^${app}$"; then
        echo "✔ $app already installed"
    else
        echo "➤ installing $app"
        flatpak install -y --noninteractive flathub $app
    fi
done

echo "🎉 Installation script is completed!"