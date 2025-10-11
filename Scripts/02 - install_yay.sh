#!/usr/bin/env bash

set -e

# ========================================================== >> AUR Helper
git clone https://aur.archlinux.org/yay.git
cd yay
makepkg -si
cd ..
rm -rf yay
