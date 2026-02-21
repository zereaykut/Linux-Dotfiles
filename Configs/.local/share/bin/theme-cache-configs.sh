#!/usr/bin/env bash

# Cache theme condigs

source $HOME/.local/share/bin/global.sh

mkdir -p $WAYDOTS_CACHE/configs

# window manager
SESSION="${XDG_CURRENT_DESKTOP,,}${DESKTOP_SESSION,,}"
if [[ "$SESSION" == *"hyprland"* ]]; then
    echo "Detected Hyprland session"
    cp -f $HOME/.config/hypr/hyprland/theme.conf $WAYDOTS_CACHE/configs/hypr.theme
elif [[ "$SESSION" == *"niri"* ]]; then
    echo "Detected Niri session"
    cp -f $HOME/.config/niri/modules/theme.kdl $WAYDOTS_CACHE/configs/niri.theme
else
    echo "Unknown session ('${SESSION}')"
fi

# hyprlock
cp -f $HOME/.config/hypr/hyprlock/theme.conf $WAYDOTS_CACHE/configs/hyprlock.theme

# rofi
cp -f $HOME/.config/rofi/theme.rasi $WAYDOTS_CACHE/configs/rofi.theme

# kitty
cp -f $HOME/.config/kitty/theme.conf $WAYDOTS_CACHE/configs/kitty.theme

# gtk 2/3/4
cp -f $HOME/.gtkrc-2.0 $WAYDOTS_CACHE/configs/gtkrc_2_0.theme
cp -f $HOME/.icons/default/index.theme $WAYDOTS_CACHE/configs/index.theme
cp -f $HOME/.config/gtk-3.0/settings.ini $WAYDOTS_CACHE/configs/gtk_3_settings.theme
cp -f $HOME/.config/gtk-4.0/settings.ini $WAYDOTS_CACHE/configs/gtk_4_settings.theme

# waybar
cp -f $HOME/.config/waybar/theme.css $WAYDOTS_CACHE/configs/waybar.theme

# kvantum
cp -f $HOME/.config/Kvantum/kv_theme/kv_theme.svg $WAYDOTS_CACHE/configs/kvantum/kvantum.theme 
cp -f $HOME/.config/Kvantum/kv_theme/kv_theme.kvconfig $WAYDOTS_CACHE/configs/kvantum/kvconfig.theme 

# qt
cp -f $HOME/.config/qt5ct/qt5ct.conf $WAYDOTS_CACHE/configs/qt5ct.theme
cp -f $HOME/.config/qt6ct/qt6ct.conf $WAYDOTS_CACHE/configs/qt6ct.theme

# kde
cp -f "$HOME/.config/kdeglobals" $WAYDOTS_CACHE/configs/kdeglobals.theme

# xsettings
cp -f "$HOME/.config/xsettingsd/xsettingsd.conf" $WAYDOTS_CACHE/configs/xsettingsd.theme

# wlogout
cp -f $HOME/.config/wlogout/theme.css $WAYDOTS_CACHE/configs/wlogout.theme

# swaync
cp -f $HOME/.config/swaync/theme.css $WAYDOTS_CACHE/configs/swaync.theme

# swayosd
cp -f $HOME/.config/swayosd/theme.css $WAYDOTS_CACHE/configs/swayosd.theme

# btop
cp -f $HOME/.config/btop/themes/btop.theme $WAYDOTS_CACHE/configs/btop.theme

exit 0
