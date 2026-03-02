#!/usr/bin/env bash

source $HOME/.local/share/bin/global.sh

# Test
# theme="${'Catppuccin Mocha':-$1}"
# wall_select="${"$theme_path/Catppuccin Mocha.png":-$2}"

theme="${1}"
theme_path="$WAYDOTS_PATH/themes/$theme/"
wall_select="${2}"
config_path="$WAYDOTS_PATH/configs/"

source $theme_path/variables.sh

# Export variables so envsubst can see them
export HYPRCURSOR_THEME=$CURSOR_THEME
export HYPRCURSOR_SIZE=$CURSOR_SIZE
export XCURSOR_THEME=$CURSOR_THEME
export XCURSOR_SIZE=$CURSOR_SIZE
export GTK_THEME ICON_THEME USER

# Define which variables envsubst is allowed to replace
# This prevents it from breaking other $VARS that might be in your config files
VARS='$CURSOR_THEME $ICON_THEME $GTK_THEME $CURSOR_SIZE $USER'

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
    $SOURCE_PATH/generate-niri-config.sh
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
wall-switcher.sh "$wall_select"

# gtk 2/3/4
envsubst "$VARS" < "$config_path/gtkrc_2_0.theme" > "$HOME/.gtkrc-2.0"
envsubst "$VARS" < "$config_path/index.theme" > "$HOME/.icons/default/index.theme"
envsubst "$VARS" < "$config_path/gtk_3_settings.theme" > "$HOME/.config/gtk-3.0/settings.ini"
envsubst "$VARS" < "$config_path/gtk_4_settings.theme" > "$HOME/.config/gtk-4.0/settings.ini"

# waybar
cp -f $theme_path/waybar.theme $HOME/.config/waybar/theme.css
cp -f $theme_path/waybar_clock.theme $HOME/.config/waybar/modules/clock.jsonc
start-top-bar.sh

# vicinae
cp -f $theme_path/vicinae.theme $HOME/.local/share/vicinae/themes/waydots.toml
start-app-launcher-daemon.sh
vicinae theme set waydots

# kvantum
cp -f $theme_path/kvantum/kvantum.theme $HOME/.config/Kvantum/kv_theme/kv_theme.svg
cp -f $theme_path/kvantum/kvconfig.theme $HOME/.config/Kvantum/kv_theme/kv_theme.kvconfig

# qt
envsubst "$VARS" < "$config_path/qt5ct.theme" > "$HOME/.config/qt5ct/qt5ct.conf"
envsubst "$VARS" < "$config_path/qt6ct.theme" > "$HOME/.config/qt6ct/qt6ct.conf"

# kde
envsubst "$VARS" < "$config_path/kdeglobals.theme" > "$HOME/.config/kdeglobals"

# xsettings
envsubst "$VARS" < "$config_path/xsettingsd.theme" > "$HOME/.config/xsettingsd/xsettingsd.conf"

# wlogout
cp -f $theme_path/wlogout.theme $HOME/.config/wlogout/theme.css

# swaync
cp -f $theme_path/swaync.theme $HOME/.config/swaync/theme.css
start-notifications-daemon.sh

# swayosd
cp -f $theme_path/swayosd.theme $HOME/.config/swayosd/theme.css
start-osd.sh

# hyprlock
theme-lock-cache.sh "$wall_select"

# btop
envsubst "$VARS" < "$config_path/btop.theme" > "$HOME/.config/btop/btop.conf"
cp -f $theme_path/btop.theme $HOME/.config/btop/themes/btop.theme

# cache variables
mkdir -p $WAYDOTS_CACHE

cat << EOF > $WAYDOTS_CACHE/theme.sh
#!/usr/bin/env bash
theme="$theme"
EOF

cat << EOF > $WAYDOTS_CACHE/wall-select.sh
#!/usr/bin/env bash
wall_select="$wall_select"
EOF