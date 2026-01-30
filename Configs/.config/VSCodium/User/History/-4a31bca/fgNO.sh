#!/usr/bin/env bash

PACKAGES_PACMAN=(
    # ========================================================== >> Base Packages
    "git"                         # version control
    "base-devel"                  # essential build tools

    # ========================================================== >> System
    "uwsm"                        # A standalone Wayland session manager

    # ========================================================== >> Dependencies
    "jq"                          # JSON processing
    "imagemagick"                 # image processing
    "libnotify"                   # desktop notifications
    "parallel"                    # parallel command execution

    # ========================================================== >> Python
    "python"                      # python interpreter
    "python-pip"                  # python package manager
    "python-psutil"               # system resource info module
    "python-pillow"               # image processing python lib
    "pyenv"                       # python version manager

    # ========================================================== >> Window Manager
    "hyprland"                    # Hyprland window manager
    "xdg-desktop-portal-hyprland" # xdg portal for hyprland
    "xdg-desktop-portal-gtk"      # GTK portal interface
    "hypridle"                    # idle management
    "hyprlock"                    # screen lock
    "hyprpicker"                  # color picker
    "niri"                        # Niri window manager
    "xwayland-satellite"          # run X11 applications under Wayland compositors (its for niri)
    "xdg-desktop-portal-wlr"      # provides screen sharing, window sharing, and screenshot support for Wayland (its for niri's screensharing feature)

    # ========================================================== >> Authentication
    "polkit-gnome"                # auth agent

    # ========================================================== >> Login Manager
    "sddm"                        # display/login manager

    # ========================================================== >> Screen Brightness
    "brightnessctl"               # brightness control

    # ========================================================== >> Bluetooth
    "bluez"                       # bluetooth stack
    "bluez-utils"                 # bluetooth utilities
    "blueman"                     # bluetooth GUI

    # ========================================================== >> Audio
    "pipewire"                    # audio/video server
    "pipewire-alsa"               # ALSA support
    "pipewire-jack"               # JACK support
    "pipewire-pulse"              # PulseAudio replacement
    "gst-plugin-pipewire"         # gstreamer integration
    "libpulse"                    # pulseaudio client library
    "sof-firmware"                # sound firmware
    "alsa-firmware"               # alsa firmware
    "pavucontrol"                 # audio volume control UI
    "pamixer"                     # CLI mixer
    "wireplumber"                 # pipewire session manager

    # ========================================================== >> Filesystem / Partition
    "exfatprogs"                  # exfat support
    "partitionmanager"            # partition tool (KDE)

    # ========================================================== >> Top Panel
    "waybar"                      # status bar

    # ========================================================== >> Terminal Tools
    "kitty"                       # terminal emulator
    "btop"                        # system resource monitor
    "eza"                         # modern ls alternative
    "fastfetch"                   # system info
    "lazygit"                     # git TUI
    "dust"                        # disk usage visualizer
    "atuin"                       # shell history search
    "fd"                          # fast file search
    "bat"                         # cat with syntax highlight
    "zoxide"                      # smarter cd command
    "fzf"                         # fuzzy finder
    "neovim"                      # text editor
    "npm"                         # javascript package manager
    "fish"                        # interactive shell
    "fisher"                      # fish plugin manager
    "starship"                    # shell prompt
    "swww"                        # wallpaper daemon
    "udiskie"                     # automounting disks
    "figlet"                      # create characters in many different styles

    # ========================================================== >> Hyprland Plugins / Build
    "meson"                       # build system
    "cmake"                       # build system
    "cpio"                        # archiving
    "hyprwayland-scanner"         # required for hyprland plugins

    # ========================================================== >> Media
    "vlc"                         # media player
    "vlc-plugin-ffmpeg"           # codec support
    "mpv"                         # lightweight video player

    # ========================================================== >> Archive Tools
    "unzip"                       # unzip files
    "zip"                         # zip files
    "unrar"                       # unrar files
    "7zip"                        # multi-format archiver
    "ark"                         # archive GUI

    # ========================================================== >> Apps
    "bitwarden"                   # password manager
    "gimp"                        # image editor
    "gwenview"                    # image viewer
    "qbittorrent"                 # torrent client
    "thunderbird"                 # email client
    "okular"                      # document viewer
    "obsidian"                    # note-taking app
    "libreoffice-fresh"           # office suite
    "kdeconnect"                  # phone integration
    "solaar"                      # logitech device manager
    "qalculate-gtk"               # calculator
    "kwalletmanager"              # kde secret manager

    # ========================================================== >> Theming
    "nwg-look"                    # gtk theme config
    "qt5ct"                       # qt5 theme control
    "qt6ct"                       # qt6 theme control
    "kvantum"                     # qt6 theme engine
    "kvantum-qt5"                 # qt5 theme engine
    "qt5-wayland"                 # qt5 wayland support
    "qt6-wayland"                 # qt6 wayland support

    # ========================================================== >> File Manager
    "dolphin"                     # file manager
    "kservice5"                   # kde service framework
    "kde-cli-tools"               # kde CLI tools
    "kdegraphics-thumbnailers"    # file previews
    "ffmpegthumbs"                # video thumbnails
    "archlinux-xdg-menu"          # xdg app menu

    # ========================================================== >> Clipboard
    "wl-clipboard"                # clipboard tools
    # "wl-clip-persist"             # Keep Wayland clipboard even after programs close (avoids crashes)
    "cliphist"                    # clipboard manager

    # ========================================================== >> Checkupdates
    "pacman-contrib"              # update checking tools

    # ========================================================== >> Power Management
    "upower"                      # power management
    "power-profiles-daemon"       # power profiles

    # ========================================================== >> Launcher
    "rofi-wayland"                # app launcher

    # ========================================================== >> Internet / Networking
    "openvpn"                     # vpn client
    "networkmanager-openvpn"      # openvpn networkmanager plugin
    "firewalld"                   # firewall service
    "dnscrypt-proxy"              # dns privacy
    "zapret"                      # bypass DPI blocking

    # ========================================================== >> Notification
    # "dunst"                      # notification daemon
    "swaync"                      # notification daemon

    # ========================================================== >> Screen Recording / Capture
    "grim"                        # screenshot utility
    "slurp"                       # region selector
    "swappy"                      # screenshot editor
    "wf-recorder"                 # screen recorder

    # ========================================================== >> Fonts
    "ttf-font-awesome"            # icon font
    "ttf-fira-sans"               # font family
    "ttf-fira-code"               # coding font
    "ttf-firacode-nerd"           # nerd font
    "ttf-jetbrains-mono-nerd"     # nerd font
    "ttf-jetbrains-mono"          # font
    "noto-fonts-emoji"            # emoji font

    # ========================================================== >> Containerization
    "docker"                      # container platform

    # ========================================================== >> Flatpak
    "flatpak"                     # flatpak support

    # ========================================================== >> Gaming
    "gamescope"                   # game compositor
    "steam"                       # steam client
)
