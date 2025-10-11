#!/usr/bin/env bash

set -e

# ========================================================== >> Apps
flatpak install -y --noninteractive flathub com.github.tchx84.Flatseal       # manage flatpak permissions
flatpak install -y --noninteractive flathub io.github.flattool.Warehouse     # manage flatpak apps
flatpak install -y --noninteractive flathub com.brave.Browser                # Brave Browser
flatpak install -y --noninteractive flathub io.missioncenter.MissionCenter   # system monitor
flatpak install -y --noninteractive flathub it.mijorus.collector             # drag and drop files
# flatpak install -y --noninteractive flathub io.github.shiftey.Desktop        # github desktop
flatpak install -y --noninteractive flathub com.obsproject.Studio            # OBS
# flatpak install -y --noninteractive flathub io.podman_desktop.PodmanDesktop  # podman desktop
flatpak install -y --noninteractive flathub org.localsend.localsend_app      # localsend
# flatpak install -y --noninteractive flathub net.pcsx2.PCSX2                  # PS2 emulator
# flatpak install -y --noninteractive flathub org.ppsspp.PPSSPP                # PSP emulator
# flatpak install flathub io.gpt4all.gpt4all                                   # Qt based GUI for GPT4All
# flatpak install flathub com.jeffser.Alpaca                                   # an ollama client
flatpak install -y --noninteractive flathub com.protonvpn.www                # proton vpn
# flatpak install -y --noninteractive flathub me.proton.Mail                   # proton mail
flatpak install -y --noninteractive flathub org.gnome.NetworkDisplays        # cast your desktop to a remote display
flatpak install -y --noninteractive flathub us.zoom.Zoom                     # online meeting
