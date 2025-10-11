#!/usr/bin/env bash

set -e

# ========================================================== >> Base Packages
sudo pacman --needed --noconfirm -S git
sudo pacman --needed --noconfirm -S base-devel

# ========================================================== >> Dependencies
sudo pacman --needed --noconfirm -S jq               # for json processing
sudo pacman --needed --noconfirm -S imagemagick      # for image processing
sudo pacman --needed --noconfirm -S libnotify        # for notifications
sudo pacman --needed --noconfirm -S parallel         # for parallel processing

# ========================================================== >> Python
sudo pacman --needed --noconfirm -S python
sudo pacman --needed --noconfirm -S python-pip
sudo pacman --needed --noconfirm -S python-psutil
sudo pacman --needed --noconfirm -S python-pillow
# sudo pacman --needed --noconfirm -S python-rich
# sudo pacman --needed --noconfirm -S python-click
# sudo pacman --needed --noconfirm -S python-requests
# sudo pacman --needed --noconfirm -S python-pyquery
sudo pacman --needed --noconfirm -S pyenv

# ========================================================== >> Hyprland
sudo pacman --needed --noconfirm -S hyprland
sudo pacman --needed --noconfirm -S xdg-desktop-portal-hyprland
sudo pacman --needed --noconfirm -S xdg-desktop-portal-gtk
sudo pacman --needed --noconfirm -S hypridle                       # idle
sudo pacman --needed --noconfirm -S hyprlock                       # Screenlock
sudo pacman --needed --noconfirm -S hyprpicker                     # color picker

# ========================================================== >> Authentication Agent
sudo pacman --needed --noconfirm -S polkit-gnome

# ========================================================== >> Login
sudo pacman --needed --noconfirm -S sddm

# ========================================================== >> Screen Brightness
sudo pacman --needed --noconfirm -S brightnessctl

# ========================================================== >> Bluetooth
sudo pacman --needed --noconfirm -S bluez
sudo pacman --needed --noconfirm -S bluez-utils
sudo pacman --needed --noconfirm -S blueman

# ========================================================== >> Audio
sudo pacman --needed --noconfirm -S pipewire
sudo pacman --needed --noconfirm -S pipewire-alsa
sudo pacman --needed --noconfirm -S pipewire-jack
sudo pacman --needed --noconfirm -S pipewire-pulse
sudo pacman --needed --noconfirm -S gst-plugin-pipewire
sudo pacman --needed --noconfirm -S libpulse
sudo pacman --needed --noconfirm -S sof-firmware
sudo pacman --needed --noconfirm -S alsa-firmware
sudo pacman --needed --noconfirm -S pavucontrol
sudo pacman --needed --noconfirm -S pamixer
sudo pacman --needed --noconfirm -S wireplumber

# ========================================================== >> Filesystem / Partition
sudo pacman --needed --noconfirm -S exfatprogs
sudo pacman --needed --noconfirm -S partitionmanager

# ========================================================== >> Top Panel
sudo pacman --needed --noconfirm -S waybar

# ========================================================== >> Terminal
sudo pacman --needed --noconfirm -S kitty       # terminal
sudo pacman --needed --noconfirm -S btop        # system monitor
sudo pacman --needed --noconfirm -S eza         # a modern, maintained replacement for ls.
sudo pacman --needed --noconfirm -S fastfetch   # system info
sudo pacman --needed --noconfirm -S lazygit     # cli git ui
sudo pacman --needed --noconfirm -S dust        # du + rust = dust. Like du but more intuitive.
sudo pacman --needed --noconfirm -S atuin       # search shell history better
sudo pacman --needed --noconfirm -S fd          # faster, colorized alternative to find
sudo pacman --needed --noconfirm -S bat         # Smarter cat with syntax highlighting
sudo pacman --needed --noconfirm -S zoxide      # zoxide is a smarter cd command, inspired by z and autojump.
sudo pacman --needed --noconfirm -S fzf         # fuzzy finder
sudo pacman --needed --noconfirm -S neovim      # terminal text editor
sudo pacman --needed --noconfirm -S npm         # javascript package manager
sudo pacman --needed --noconfirm -S fish        # interactive terminal
sudo pacman --needed --noconfirm -S fisher      # fish plugin manager
sudo pacman --needed --noconfirm -S starship    # customizable shell prompt
sudo pacman --needed --noconfirm -S swww        # wallpaper daemon
sudo pacman --needed --noconfirm -S udiskie     # disk manager

# ========================================================== >> Hyprland Plugin
sudo pacman --needed --noconfirm -S meson
sudo pacman --needed --noconfirm -S cmake
sudo pacman --needed --noconfirm -S cpio
sudo pacman --needed --noconfirm -S hyprwayland-scanner

# ========================================================== >> Media
sudo pacman --needed --noconfirm -S vlc
sudo pacman --needed --noconfirm -S mpv

# ========================================================== >> Archive
sudo pacman --needed --noconfirm -S unzip       # extract .zip files
sudo pacman --needed --noconfirm -S unrar       # extract .rar files
sudo pacman --needed --noconfirm -S 7zip
sudo pacman --needed --noconfirm -S ark

# ========================================================== >> Apps
sudo pacman --needed --noconfirm -S bitwarden
sudo pacman --needed --noconfirm -S gimp
sudo pacman --needed --noconfirm -S gwenview
sudo pacman --needed --noconfirm -S qbittorrent
sudo pacman --needed --noconfirm -S thunderbird
sudo pacman --needed --noconfirm -S notepadqq
# sudo pacman --needed --noconfirm -S obs-studio
sudo pacman --needed --noconfirm -S okular
# sudo pacman --needed --noconfirm -S discord
sudo pacman --needed --noconfirm -S obsidian
sudo pacman --needed --noconfirm -S libreoffice-fresh
sudo pacman --needed --noconfirm -S kdeconnect
sudo pacman --needed --noconfirm -S solaar
sudo pacman --needed --noconfirm -S qalculate-gtk
sudo pacman --needed --noconfirm -S kwalletmanager
# sudo pacman --needed --noconfirm -S timeshift

# ========================================================== >> Display
sudo pacman --needed --noconfirm -S nwg-displays

# ========================================================== >> Theming
sudo pacman --needed --noconfirm -S nwg-look                     # gtk configuration tool
sudo pacman --needed --noconfirm -S qt5ct                        # qt5 configuration tool
sudo pacman --needed --noconfirm -S qt6ct                        # qt6 configuration tool
sudo pacman --needed --noconfirm -S kvantum                      # svg based qt6 theme engine
sudo pacman --needed --noconfirm -S kvantum-qt5                  # svg based qt5 theme engine
sudo pacman --needed --noconfirm -S qt5-wayland                  # wayland support in qt5
sudo pacman --needed --noconfirm -S qt6-wayland                  # wayland support in qt6

# ========================================================== >> File Manager
sudo pacman --needed --noconfirm -S dolphin
sudo pacman --needed --noconfirm -S kservice5
sudo pacman --needed --noconfirm -S kde-cli-tools
sudo pacman --needed --noconfirm -S kdegraphics-thumbnailers
sudo pacman --needed --noconfirm -S ffmpegthumbs
sudo pacman --needed --noconfirm -S archlinux-xdg-menu           # for mimeapps.list to show on dolphin

# ========================================================== >> Clipoard
sudo pacman --needed --noconfirm -S wl-clipboard
sudo pacman --needed --noconfirm -S cliphist

# ========================================================== >> Checkupdates
sudo pacman --needed --noconfirm -S pacman-contrib            # check pacman updates

# ========================================================== >> Power
sudo pacman --needed --noconfirm -S upower                    # power management
sudo pacman --needed --noconfirm -S power-profiles-daemon     # power profile daemon

# ========================================================== >> Launcher
sudo pacman --needed --noconfirm -S rofi-wayland          # dmenu and application launcher
# sudo pacman --needed --noconfirm -S nwg-drawer            # application launcher

# ========================================================== >> Internet
sudo pacman --needed --noconfirm -S openvpn               # VPN
sudo pacman --needed --noconfirm -S firewalld             # firewall manager
sudo pacman --needed --noconfirm -S dnscrypt-proxy        # DNS
sudo pacman --needed --noconfirm -S zapret                # zapret for DPI

# ========================================================== >> Notification
# sudo pacman --needed --noconfirm -S dunst                 # notification daemon
sudo pacman --needed --noconfirm -S swaync                 # notification daemon

# ========================================================== >> Screenshot
sudo pacman --needed --noconfirm -S grim                  # screenshot tool
sudo pacman --needed --noconfirm -S slurp                 # region select for screenshot/screenshare
sudo pacman --needed --noconfirm -S swappy                # screenshot editor

# ========================================================== >> Screen Recording
sudo pacman --needed --noconfirm -S wf-recorder           # screen recording tool

# ========================================================== >> Fonts
sudo pacman --needed --noconfirm -S ttf-font-awesome
sudo pacman --needed --noconfirm -S ttf-fira-sans
sudo pacman --needed --noconfirm -S ttf-fira-code
sudo pacman --needed --noconfirm -S ttf-firacode-nerd
sudo pacman --needed --noconfirm -S ttf-jetbrains-mono-nerd
sudo pacman --needed --noconfirm -S ttf-jetbrains-mono

# ========================================================== >> Containerization
sudo pacman --needed --noconfirm -S docker
# sudo pacman --needed --noconfirm -S podman

# ========================================================== >> Install Flatpak
sudo pacman --needed --noconfirm -S flatpak

# ========================================================== >> Gaming
sudo pacman --needed --noconfirm -S gamescope
sudo pacman -S steam
