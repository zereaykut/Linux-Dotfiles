#!/usr/bin/env bash

set -e

# ========================================================== >> AUR
yay --needed --noconfirm -S swayosd-git        # OSD server
yay --needed --noconfirm -S hyprshot           # screenshot
yay --needed --noconfirm -S vscodium-bin       # code editor
# yay --needed --noconfirm -S brave-bin          # browser
yay --needed --noconfirm -S pikaur             # aur helper
yay --needed --noconfirm -S wlogout            # logout menu
yay --needed --noconfirm -S smile              # emoji picker
yay --needed --noconfirm -S ventoy             # create bootable drives
yay --needed --noconfirm -S netbird            # vpn client for homelab
