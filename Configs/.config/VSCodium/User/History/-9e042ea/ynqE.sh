#!/usr/bin/env bash

##############################
# Custom PATH
##############################
SOURCE_PATH="$HOME/.local/share/bin"
export PATH="$HOME/.local/bin:$SOURCE_PATH:$PATH"

##############################
# Toolkit Backend Variables
##############################
export GDK_BACKEND="wayland,x11,*"
export GDK_SCALE="1"
export SDL_VIDEODRIVER="wayland"
export CLUTTER_BACKEND="wayland"

##############################
# XDG Specifications
##############################
export XDG_CURRENT_DESKTOP="Hyprland"
export XDG_SESSION_TYPE="wayland"
export XDG_SESSION_DESKTOP="Hyprland"

##############################
# Qt Variables
##############################
export QT_QPA_PLATFORM="wayland;xcb"
export QT_QPA_PLATFORMTHEME="qt6ct"
export QT_WAYLAND_DISABLE_WINDOWDECORATION="1"
export QT_AUTO_SCREEN_SCALE_FACTOR="1"

##############################
# Hyprshot
##############################
export HYPRSHOT_DIR="$HOME/Pictures/Screenshots"

##############################
# Mozilla
##############################
export MOZ_ENABLE_WAYLAND="1"

##############################
# Electron
##############################
export ELECTRON_ENABLE_WAYLAND="1"
export ELECTRON_OZONE_PLATFORM_HINT="wayland"

##############################
# AppImage Launcher
##############################
export APPIMAGELAUNCHER_DISABLE="1"

##############################
# Ozone
##############################
export OZONE_PLATFORM="wayland"

##############################
# NVIDIA (commented out)
##############################
# export LIBVA_DRIVER_NAME="nvidia"
# export GBM_BACKEND="nvidia-drm"
# export __GLX_VENDOR_LIBRARY_NAME="nvidia"
# export __GL_VRR_ALLOWED="1"
# export WLR_DRM_NO_ATOMIC="1"

# --- Ensure scripts are executable ---
chmod +x "$SOURCE_PATH/reset_xdg_portal.sh" 2>/dev/null
chmod +x "$SOURCE_PATH/theme_reload.sh" 2>/dev/null

# --- Autostart Programs & Services ---

# Reset XDPH for screen sharing
"$SOURCE_PATH/reset_xdg_portal.sh" &

# XDPH environment updates
dbus-update-activation-environment --systemd WAYLAND_DISPLAY XDG_CURRENT_DESKTOP &
dbus-update-activation-environment --systemd --all &
systemctl --user import-environment WAYLAND_DISPLAY XDG_CURRENT_DESKTOP &

# Top bas/panel (Waybar)
$SOURCE_PATH/launch_top_bar.sh

# Wallpaper daemon
swww-daemon &
swww restore &

# Clipboard manager
wl-paste --watch cliphist store &

# Notification daemon
swaync &

# Auth agent
/usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1 &

# Network manager applet
nm-applet --indicator &

# Bluetooth applet
blueman-applet &

# External drive manager
udiskie --no-automount --smart-tray &

# Idle daemon
hypridle &

# On-screen display server
swayosd-server &

# KDE connect (optional)
# kdeconnect-cli &

# Clear clipboard on startup (optional)
# cliphist wipe &

# Rebuild KDE menus
XDG_MENU_PREFIX=arch- kbuildsycoca6 &

# Theme reload script
"$SOURCE_PATH/theme_reload.sh" &

exit 0
