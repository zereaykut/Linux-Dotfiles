#!/bin/env bash

SOURCE_PATH="$HOME/.local/share/bin"

# theme="${'Catppuccin Mocha':-$1}"
# wall_select="${"$theme_path/Catppuccin Mocha.png":-$2}"

theme="${1}"
theme_path="$HOME/.config/waydots/themes/$theme/"
wall_select="${2}"
config_path="$HOME/.config/waydots/configs/"
cache_path="$HOME/.cache/waydots"

source $theme_path/variables.sh

# environment variables
export HYPRCURSOR_THEME=$CURSOR_THEME
export HYPRCURSOR_SIZE=$CURSOR_SIZE
export XCURSOR_THEME=$CURSOR_THEME
export XCURSOR_SIZE=$CURSOR_SIZE

# gsettings
gsettings set org.gnome.desktop.interface cursor-theme "$CURSOR_THEME"
gsettings set org.gnome.desktop.interface cursor-size $CURSOR_SIZE
gsettings set org.gnome.desktop.interface icon-theme "$ICON_THEME"
gsettings set org.gnome.desktop.interface gtk-theme "$GTK_THEME"
gsettings set org.gnome.desktop.interface color-scheme "$COLOR_SCHEME"

# window manager
SESSION="${XDG_CURRENT_DESKTOP,,}${DESKTOP_SESSION,,}"
if [[ "$SESSION" == *"hyprland"* ]]; then
    echo "Detected Hyprland session"
    cp -f $theme_path/hypr.theme $HOME/.config/hypr/hyprland/theme.conf
    hyprctl setcursor $CURSOR_THEME $CURSOR_SIZE
    hyprctl reload 
elif [[ "$SESSION" == *"niri"* ]]; then
    echo "Detected Niri session"
    cp -f $theme_path/niri.theme $HOME/.config/niri/modules/theme.kdl
    $SOURCE_PATH/generate_niri_config.sh
    niri msg reload-config
else
    echo "Unknown session ('${SESSION}')"
fi

# hyprlock
cp -f $theme_path/hyprlock.theme $HOME/.config/hypr/hyprlock/theme.conf

# rofi
cp -f $theme_path/rofi.theme $HOME/.config/rofi/theme.rasi

# kitty
cp -f $theme_path/kitty.theme $HOME/.config/kitty/theme.conf

# swww
wall_switcher.sh "$wall_select"

# gtk 2/3/4
sed "s/{CURSOR_THEME}/$CURSOR_THEME/; s/{ICON_THEME}/$ICON_THEME/; s/{GTK_THEME}/$GTK_THEME/; s/{CURSOR_SIZE}/$CURSOR_SIZE/" $config_path/gtkrc_2_0.theme > $HOME/.gtkrc-2.0
sed "s/{CURSOR_THEME}/$CURSOR_THEME/" $config_path/index.theme > $HOME/.icons/default/index.theme
sed "s/{CURSOR_THEME}/$CURSOR_THEME/; s/{ICON_THEME}/$ICON_THEME/; s/{GTK_THEME}/$GTK_THEME/; s/{CURSOR_SIZE}/$CURSOR_SIZE/" $config_path/gtk_3_settings.theme > $HOME/.config/gtk-3.0/settings.ini
sed "s/{CURSOR_THEME}/$CURSOR_THEME/; s/{ICON_THEME}/$ICON_THEME/; s/{GTK_THEME}/$GTK_THEME/; s/{CURSOR_SIZE}/$CURSOR_SIZE/" $config_path/gtk_4_settings.theme > $HOME/.config/gtk-4.0/settings.ini

# waybar
cp -f $theme_path/waybar.theme $HOME/.config/waybar/theme.css
$SOURCE_PATH/launch_top_bar.sh

# kvantum
cp -f $theme_path/kvantum/kvantum.theme $HOME/.config/Kvantum/kv_theme/kv_theme.svg
cp -f $theme_path/kvantum/kvconfig.theme $HOME/.config/Kvantum/kv_theme/kv_theme.kvconfig

# qt
sed "s/{ICON_THEME}/$ICON_THEME/" $config_path/qt5ct.theme > $HOME/.config/qt5ct/qt5ct.conf
sed "s/{ICON_THEME}/$ICON_THEME/" $config_path/qt6ct.theme > $HOME/.config/qt6ct/qt6ct.conf

# kde
sed "s/{ICON_THEME}/$ICON_THEME/" $config_path/kdeglobals.theme > $HOME/.config/kdeglobals

# xsettings
sed "s/{CURSOR_THEME}/$CURSOR_THEME/; s/{ICON_THEME}/$ICON_THEME/; s/{GTK_THEME}/$GTK_THEME/" $config_path/xsettingsd.theme > $HOME/.config/xsettingsd/xsettingsd.conf

# wlogout
cp -f $theme_path/wlogout.theme $HOME/.config/wlogout/theme.css

# swaync
cp -f $theme_path/swaync.theme $HOME/.config/swaync/theme.css
$SOURCE_PATH/launch_notification_daemon.sh

# swayosd
cp -f $theme_path/swayosd.theme $HOME/.config/swayosd/theme.css
$SOURCE_PATH/launch_osd.sh

# hyprlock
# cp -f $wall_select $HOME/.cache/themes/lock_screen.png
theme_lock_cache.sh "$wall_select"

# btop
sed "s/{USER}/$USER/" $config_path/btop.theme > $HOME/.config/btop/btop.conf
cp -f $theme_path/btop.theme $HOME/.config/btop/themes/btop.theme

# overview
cp -f $theme_path/hyprland-overview.theme $HOME/.config/hyprland-overview/style.qss

# cache variables
mkdir -p $cache_path

cat << EOF > $cache_path/theme.sh
#!/bin/env bash
theme="$theme"
EOF

cat << EOF > $cache_path/wall_select.sh
#!/bin/env bash
wall_select="$wall_select"
EOF