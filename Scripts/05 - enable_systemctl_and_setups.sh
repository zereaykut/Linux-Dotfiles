#!/usr/bin/env bash

set -e

# ========================================================== >> Enable Systemctl
sudo systemctl enable sddm                                     # login manager
sudo systemctl enable bluetooth                                # bluetooth
systemctl enable --user pipewire-pulse.service                 # audio
sudo systemctl enable --now swayosd-libinput-backend.service   # swayosd
sudo systemctl enable firewalld.service                        # firewall

# ========================================================== >> Flatpak
sudo flatpak override --filesystem=$HOME/.themes
sudo flatpak override --filesystem=$HOME/.icons

# ========================================================== >> Grub
sudo usermod -aG input $(whoami)   # Adds used user to input group for waybar keyboard-state widget to work
sudo usermod -aG video $(whoami)   

# ========================================================== >> resolved (DNS)
sudo systemctl enable systemd-resolved
sudo systemctl start systemd-resolved

# ========================================================== >> zapret
sudo systemctl enable zapret
sudo systemctl start zapret

# ========================================================== >> Shell
chsh -s $(which fish)

# ========================================================== >> Hyprland Plugins
hyprpm update
hyprpm add https://github.com/hyprwm/hyprland-plugins
hyprpm enable hyprexpo

# hyprpm add https://github.com/raybbian/hyprtasking
# hyprpm enable hyprtasking

# hyprpm add https://github.com/KZDKM/Hyprspace
# hyprpm enable Hyprspace
