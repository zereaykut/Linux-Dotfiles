#!/usr/bin/env bash

source $HOME/.local/share/bin/global.sh

wall_select="${1}"

swww img "$wall_select" --transition-type center --transition-fps 60 --transition-duration 3

# swww img -o "eDP-1" "$wall_select" --transition-type center --transition-fps 60 --transition-duration 3
# swww img -o "HDMI-A-1" "$wall_select" --transition-type center --transition-fps 60 --transition-duration 3

mkdir -p $WAYDOTS_CACHE

cat << EOF > $WAYDOTS_CACHE/wall-select.sh
#!/usr/bin/env bash
wall_select="$wall_select"
EOF