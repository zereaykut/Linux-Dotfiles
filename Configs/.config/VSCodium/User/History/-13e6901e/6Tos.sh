#!/bin/env bash

SDDM_PATH="/usr/share/sddm/"
sddm_waydots="$SDDM_PATH/themes/SDDM-waydots/"
rofi_conf="$HOME/.config/rofi/theme_select.rasi"
sddm_cache_path="/$HOME/.cache/waydots/theme_sddm_previews/$theme/"

mkdir -p $sddm_cache_path

mapfile -d '' PICS < <(find "$sddm_waydots/themes" -maxdepth 2 -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.gif" \) -print0)

# Rofi command
rofi_command="rofi -i -show -dmenu -config $rofi_conf"

# Sorting Wallpapers
menu() {
    # Sort the PICS array
    IFS=$'\n' sorted_options=($(sort <<<"${PICS[*]}"))

    for pic_path in "${sorted_options[@]}"; do
        pic_name=$(basename "$pic_path")

        # If it's a GIF, extract the first frame as a temporary file
        # if [[ "$pic_name" =~ \.gif$ ]]; then
        cached_pic="$sddm_cache_path/$(basename "$pic_path" .gif).png"

        # Check if the cached version already exists
        if [[ ! -f "$cached_pic" ]]; then
            # echo "Creating cached first frame for GIF: $pic_name"
            # Extract first frame if it doesn't exist
            magick "$pic_path"[0] -resize 480x270\! "$cached_pic"
        fi
        pic_path="$cached_pic" # Replace GIF with cached first frame PNG
        # fi

        # Displaying the image path or file name
        printf "%s\x00icon\x1f%s\n" "$(echo "$pic_name" | cut -d. -f1)" "$pic_path"
    done
}

# Choice of wallpapers
main() {
    choice=$(menu | $rofi_command)

    # Trim any potential whitespace or hidden characters
    choice=$(echo "$choice" | xargs)
    # RANDOM_PIC_NAME=$(echo "$RANDOM_PIC_NAME" | xargs)
    echo $choice
    # No choice case
    if [[ -z "$choice" ]]; then
        echo "No choice selected. Exiting."
        exit 0
    fi

    # Find the index of the selected file
    pic_index=-1
    for i in "${!PICS[@]}"; do
        filename=$(basename "${PICS[$i]}")
        if [[ "$filename" == "$choice"* ]]; then
            pic_index=$i
            break
        fi
    done

    # Check if a wallpaper was selected
    if [ -n "$choice" ]; then
        # Change SDDM theme config
        pkexec cp -f "$sddm_waydots/themes/$choice/theme.conf" "$sddm_waydots/theme.conf"
    else
        echo "No SDDM theme selected."
        exit 1
    fi
}

main
