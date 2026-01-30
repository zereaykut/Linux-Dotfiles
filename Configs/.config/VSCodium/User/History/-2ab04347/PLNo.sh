#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(dirname "$(realpath "$0")")
LOGFILE="$SCRIPT_DIR/install.log"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S')  $*" | tee -a "$LOGFILE"
}

# ========================================================== >> Create Folders
create_folders() {
    log "=== Creating folders ==="
    mkdir -p ~/.config
    mkdir -p ~/.local/share/{bin,waybar,themes}
    mkdir -p ~/Projects ~/Documents ~/Downloads ~/Videos
    mkdir -p ~/Pictures/Screenshots
    mkdir -p ~/Torrent/{torrents,torrent_files,finished_torrents/{Movie,TV,Music,Other},finished_torrent_files,watched_torrent_files}
    log "Folders created successfully"
}

# ========================================================== >> Configs
copy_configs() {
    log "=== Copying configs ==="
    cp -rf "$SCRIPT_DIR/../Configs/.config/"* ~/.config/
    cp -rf "$SCRIPT_DIR/../Configs/.local/share/"* ~/.local/share/
    log "Configs copied successfully"
}

# ========================================================== >> SDDM
setup_sddm() {
    log "=== Setting up SDDM ==="
    sudo mv "$SCRIPT_DIR/../Move/sddm/sddm.conf" /etc/
    sudo mkdir -p /usr/share/sddm/themes/SDDM-hyprdots
    sudo cp -rf "$SCRIPT_DIR/../Move/sddm/SDDM-hyprdots/"* /usr/share/sddm/themes/SDDM-hyprdots/
    log "SDDM setup completed"
}

# ========================================================== >> Cursor
setup_cursor() {
    log "=== Setting up cursor ==="
    sudo mv "$SCRIPT_DIR/../Move/icons_default/index.theme" /usr/share/icons/default/index.theme
    log "Cursor theme applied"
}

# ========================================================== >> GRUB
setup_grub() {
    log "=== Setting up GRUB ==="
    sudo mv "$SCRIPT_DIR/../Move/grub/grub.conf" /etc/default/grub
    sudo mv "$SCRIPT_DIR/../Move/grub/grub_background.png" /boot/grub/
    sudo grub-mkconfig -o /boot/grub/grub.cfg
    log "GRUB configured successfully"
}

# ========================================================== >> systemd-resolved
setup_resolved() {
    log "=== Setting up systemd-resolved ==="
    sudo mv "$SCRIPT_DIR/../Move/systemd-resolved/resolved.conf" /etc/systemd/resolved.conf
    sudo ln -sf /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf
    log "systemd-resolved configured successfully"
}

# ========================================================== >> zapret
setup_zapret() {
    log "=== Setting up Zapret ==="
    sudo mv "$SCRIPT_DIR/../Move/zapret/config" /opt/zapret/config
    log "Zapret setup completed"
}