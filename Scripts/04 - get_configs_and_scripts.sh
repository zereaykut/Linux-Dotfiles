#!/usr/bin/env bash

set -e

# ========================================================== >> Create Folders
mkdir -p ~/.config
mkdir -p ~/.local/share/{bin,waybar,themes}
mkdir -p ~/Projects ~/Documents ~/Downloads ~/Videos
mkdir -p ~/Pictures/Screenshots
mkdir -p ~/Torrent/{torrents,torrent_files,finished_torrents/{Movie,TV,Music,Comic,Animation,Other},finished_torrent_files,watched_torrent_files}

# ========================================================== >> Configs
cp -rf ../Configs/.config/* ~/.config/

# ========================================================== >> Scripts
cp -rf ../Configs/.local/share/bin/* ~/.local/share/bin/

# ========================================================== >> SDDM
sudo mv ../Move/sddm/sddm.conf /etc/.
sudo mkdir /usr/share/sddm/themes/SDDM-hyprdots
sudo cp -rf ../Move/sddm/SDDM-hyprdots/* /usr/share/sddm/themes/SDDM-hyprdots/

# ========================================================== >> Cursor
sudo mv ../Move/icons_default/index.theme /usr//share/icons/default/index.theme

# ========================================================== >> Grub
sudo mv ../Move/grub/grub.conf /etc/default/grub
sudo mv ../Move/grub/grub_background.png /boot/grub/.
sudo grub-mkconfig -o /boot/grub/grub.cfg

# ========================================================== >> resolved (DNS)
sudo mv ../Move/systemd-resolved/resolved.conf /etc/systemd/resolved.conf
sudo ln -sf /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf        # Make /etc/resolv.conf a symlink to Systemd-Resolved file

# ========================================================== >> zapret
sudo mv ../Move/zapret/config /opt/zapret/config
