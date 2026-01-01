#!/usr/bin/env bash

SCRIPT_DIR="$(dirname "$(realpath "$0")")"
source "$SCRIPT_DIR/global_fn.sh"

# ========================================================== >> GTK Themes
install_gtk_themes() {
    log "=== Installing GTK themes ==="

    mkdir -p ~/.themes
    sudo mkdir -p /usr/share/themes

    srcGtk="$SCRIPT_DIR/../Source/Gtk"

    for file in "$srcGtk"/*.tar.gz; do
        [ -e "$file" ] || continue  # skip if no files
        log "Extracting $file"
        tar -xvzf "$file" -C ~/.themes/
        sudo tar -xvzf "$file" -C /usr/share/themes/
    done

    log "GTK themes installed"
}

# ========================================================== >> Icons
install_icons() {
    log "=== Installing icons ==="

    mkdir -p ~/.icons
    sudo mkdir -p /usr/share/icons

    srcIcon="$SCRIPT_DIR/../Source/Icon"

    for file in "$srcIcon"/*.tar.gz; do
        [ -e "$file" ] || continue
        log "Extracting $file"
        tar -xvzf "$file" -C ~/.icons/
        sudo tar -xvzf "$file" -C /usr/share/icons/
    done

    log "Icons installed"
}

# ========================================================== >> Cursors
install_cursors() {
    log "=== Installing cursors ==="

    mkdir -p ~/.icons
    sudo mkdir -p /usr/share/icons

    srcCursor="$SCRIPT_DIR/../Source/Cursor"

    for file in "$srcCursor"/*.tar.gz; do
        [ -e "$file" ] || continue
        log "Extracting $file"
        tar -xvzf "$file" -C ~/.icons/
        sudo tar -xvzf "$file" -C /usr/share/icons/
    done

    log "Cursors installed"
}
