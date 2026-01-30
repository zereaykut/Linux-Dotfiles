#!/usr/bin/env bash

PACKAGES_DNF=(
    # Base
    git
    @development-tools
    jq
    ImageMagick
    libnotify
    parallel

    # Python
    python3
    python3-pip
    python3-psutil
    python3-pillow
    pyenv

    # Hyprland
    hyprland
    xdg-desktop-portal-hyprland
    xdg-desktop-portal-gtk
    hypridle
    hyprlock
    hyprpicker

    # Authentication
    polkit-gnome

    # Display Manager
    sddm

    # Screen brightness
    brightnessctl

    # Bluetooth
    bluez
    bluez-tools
    blueman

    # Audio (PipeWire)
    pipewire
    pipewire-alsa
    pipewire-jack-audio-connection-kit
    pipewire-pulseaudio
    gstreamer1-plugin-pipewire
    alsa-firmware
    pavucontrol
    pamixer
    wireplumber

    # FS
    exfatprogs
    partitionmanager

    # Panel
    waybar

    # Terminal tools
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
    swww
    udiskie

    # Build
    meson
    cmake
    cpio

    # Media
    vlc
    mpv

    # Archive Tools
    unzip
    unrar
    p7zip
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
    kvantum
    qt5-qtwayland
    qt6-qtwayland

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
    # zapret (Fedora’da repo yok, flatpak/COPR gerekirse eklenebilir)

    # Notification
    swaync

    # Screenshot
    grim
    slurp
    swappy

    # Screen Recording
    wf-recorder

    # Fonts
    fontawesome-fonts
    fira-code-fonts
    jetbrains-mono-fonts
    jetbrains-mono-nerd-fonts

    # Containers
    docker

    # Flatpak
    flatpak

    # Gaming
    gamescope
    steam
)
