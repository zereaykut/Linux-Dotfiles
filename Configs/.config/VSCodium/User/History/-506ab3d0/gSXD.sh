#!/usr/bin/env bash
set -e

# Load package list
source ./Packages/arch_pacman.sh

echo ">>> Checking already installed packages..."

# Filter out installed packages
MISSING_PACKAGES=()
for pkg in "${PACKAGES[@]}"; do
    if pacman -Qi "$pkg" &>/dev/null; then
        echo "✔ $pkg already installed"
    else
        echo "➤ $pkg missing"
        MISSING_PACKAGES+=("$pkg")
    fi
done

# Install only missing packages
if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo
    echo ">>> Installing missing packages:"
    printf '%s\n' "${MISSING_PACKAGES[@]}"
    echo

    sudo pacman --needed --noconfirm -S "${MISSING_PACKAGES[@]}"
else
    echo "🎉 All packages are already installed!"
fi
