#!/usr/bin/env bash

PACKAGES_APT=(
    # Base / Tools
    git
    build-essential
    jq
    imagemagick
    libnotify-bin
    parallel

    # Python
    python3
    python3-pip
    python3-psutil
    python3-pil       # pillow
    pyenv

    # Hyprland (resmi repo yok, PPA ile eklenebilir)
    hyprland          # ppa:hyprland-dev/unstable gerekli

    xdg-desktop-portal
    xdg-desktop-portal-gtk
    # hypridle/hyprlock/hyprpicker → PPA paketlerinden kurulacak

    # Authentication
    policykit-1-gnome

    # Login Manager
    sddm

    # Screen brightness
    brightnessctl

    # Bluetooth
    bluez
    bluez-tools
    blueman

    # Audio
    pipewire
    pipewire-audio
    pipewire-pulse
    pipewire-jack
    libspa-0.2-bluetooth
    pavucontrol
    pamixer

    # System FS
    exfatprogs
    partitionmanager

    # Panel
    waybar

    # Terminal Tools
    kitty
    btop
    eza
    fastfetch
    lazygit
    dust
    atuin
    fd-find
    bat
    zoxide
    fzf
    neovim
    npm
    fish
    starship
    udiskie

    # Build Tools
    meson
    cmake
    cpio

    # Media
    vlc
    mpv

    # Archive
    unzip
    unrar
    p7zip-full
    ark

    # Apps
    bitwarden
    gimp
    gwenview
    qbittorrent
    thunderbird
    okular
    libreoffice
    kdeconnect
    solaar
    qalculate-gtk
    kwalletmanager

    # Display config
    nwg-displays

    # Theming
    nwg-look
    qt5ct
    qt6ct
    kvantum-manager
    qtwayland5
    qt6-wayland

    # File Manager
    dolphin
    kde-cli-tools
    kdegraphics-thumbnailers
    ffmpegthumbs

    # Clipboard
    wl-clipboard
    cliphist

    # Power
    upower
    power-profiles-daemon

    # Launcher
    rofi-wayland

    # Networking
    openvpn
    firewalld
    dnscrypt-proxy

    # Notification
    swaync

    # Screenshot
    grim
    slurp
    swappy

    # Screen Recording
    wf-recorder

    # Fonts
    fonts-font-awesome
    fonts-firacode
    fonts-jetbrains-mono

    # Containers
    docker.io

    # Flatpak
    flatpak

    # Gaming
    gamescope
    steam-installer
)
