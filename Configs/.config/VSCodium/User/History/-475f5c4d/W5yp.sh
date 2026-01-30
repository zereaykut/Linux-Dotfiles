#!/usr/bin/env bash

# source = https://github.com/HyDE-Project/HyDE

# Script to configure and launch wlogout with custom layout and style options based on user input.
# It supports two modes: "dark" (style_1.css, layout_1) and "light" (style_2.css, layout_2).
# If wlogout is already running, it terminates the existing process before starting a new one.

print_error() {
    local cmd
    cmd=$(basename "$0")
    cat <<EOF
    "${cmd}" <action> [step]
    ...valid actions are...
        1 dark -- use style_1.css and layout_1 dark button colors
        2 light -- use style_2.css and layout_2 light button colors (default is dark)

    Example:
        "${cmd}" 1      # use style_1.css and layout_1
        "${cmd}" 2      # use style_2.css and layout_2
EOF
}

# Check if wlogout is already running
if pgrep -x "wlogout" >/dev/null; then
    pkill -x "wlogout"
    exit 0
fi

# Set file variables
wlogoutStyle="${1}"
wlogoutStyle=${wlogoutStyle:-1}
confDir="${confDir:-$HOME/.config}"
wLayout="${confDir}/wlogout/layout_${wlogoutStyle}"
wlTmplt="${confDir}/wlogout/style_${wlogoutStyle}.css"
echo "wlogoutStyle: ${wlogoutStyle}"
echo "wLayout: ${wLayout}"
echo "wlTmplt: ${wlTmplt}"

if [ ! -f "${wLayout}" ] || [ ! -f "${wlTmplt}" ]; then
    echo "ERROR: Config ${wlogoutStyle} not found..."
    wlogoutStyle=1
    wLayout="${confDir}/wlogout/layout_${wlogoutStyle}"
    wlTmplt="${confDir}/wlogout/style_${wlogoutStyle}.css"
fi



# Detect monitor res
# x_mon=$(hyprctl -j monitors | jq '.[] | select(.focused==true) | .width')
# y_mon=$(hyprctl -j monitors | jq '.[] | select(.focused==true) | .height')
# hypr_scale=$(hyprctl -j monitors | jq '.[] | select (.focused == true) | .scale' | sed 's/\.//')
x_mon=1920
y_mon=1080
hypr_scale=100
# Scale config layout and style

case "${wlogoutStyle}" in
1)
    wlColms=6
    export mgn=$((y_mon * 28 / hypr_scale))
    export hvr=$((y_mon * 23 / hypr_scale))
    ;;
2)
    wlColms=2
    export x_mgn=$((x_mon * 35 / hypr_scale))
    export y_mgn=$((y_mon * 25 / hypr_scale))
    export x_hvr=$((x_mon * 32 / hypr_scale))
    export y_hvr=$((y_mon * 20 / hypr_scale))
    ;;
esac

#// scale font size

export fntSize=$((y_mon * 2 / 100))

dcol_mode="${2:-dark}"

#  Theme mode: detects the color-scheme set in hypr.theme and falls back if nothing is parsed.

{ [ "${dcol_mode}" == "dark" ] && export BtnCol="white"; } || export BtnCol="black"

#// eval hypr border radius

hypr_border="${3:-10}"
export active_rad=$((hypr_border * 5))
export button_rad=$((hypr_border * 8))

#// eval config files

wlStyle="$(envsubst <"${wlTmplt}")"

#// launch wlogout
case $1 in
    1 | 2)
        wlogout -b "${wlColms}" -c 0 -r 0 -m 0 --layout "${wLayout}" --css <(echo "${wlStyle}") --protocol layer-shell
        ;;
    *)
        print_error ;;
esac
