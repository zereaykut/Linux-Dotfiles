#!/bin/env bash
cache_path="$HOME/.cache/waydots"
wall_select="${1}"

swww img "$wall_select" --transition-type center --transition-fps 60 --transition-duration 3

# swww img -o "eDP-1" "$wall_select" --transition-type center --transition-fps 60 --transition-duration 3
# swww img -o "HDMI-A-1" "$wall_select" --transition-type center --transition-fps 60 --transition-duration 3

mkdir -p $cache_path

cat << EOF > $cache_path/wall_select.sh
#!/bin/env bash
wall_select="$wall_select"
EOF