#!/usr/bin/env bash

set -e

# ========================================================== >> Pacman
#sudo mv ../Move/pacman/pacman.conf /etc/.

# ========================================================== >> Chaotic - Aur
# Rtrieve the primary key to enable the installation of chaotic aur keyring and mirror list. 
sudo pacman-key --recv-key 3056513887B78AEB --keyserver keyserver.ubuntu.com
sudo pacman-key --lsign-key 3056513887B78AEB

# Install chaotic-keyring and chaotic-mirrorlist packages. 
sudo pacman --needed --noconfirm -U 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-keyring.pkg.tar.zst'
sudo pacman --needed --noconfirm -U 'https://cdn-mirror.chaotic.cx/chaotic-aur/chaotic-mirrorlist.pkg.tar.zst'

# Get pacman.conf with chaotic aur
cp ../Move/pacman/pacman_chaotic_aur.conf /etc/pacman.conf

# Run full system update
sudo pacman --needed --noconfirm -Syu

# ========================================================== >> Yay & Pikaur
# sudo pacman --needed --noconfirm -S yay
# sudo pacman --needed --noconfirm -S pikaur
