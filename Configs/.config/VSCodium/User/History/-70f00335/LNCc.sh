#!/bin/env bash

# Define paths
themes_path="$HOME/.config/waydots/themes/"
rofi_conf="$HOME/.config/rofi/theme_select.rasi"
cache_path="$HOME/.cache/waydots/theme_previews/"
mkdir -p "$cache_path"

# Retrieve image files
mapfile -d '' PICS < <(find "$themes_path" -maxdepth 2 -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.gif" \) -print0)

# Rofi command
rofi_command="rofi -i -show -dmenu -config $rofi_conf"

# Sorting and Menu Generation
menu() {
    # Sort the PICS array
    IFS=$'\n' sorted_options=($(sort <<<"${PICS[*]}"))

    for pic_path in "${sorted_options[@]}"; do
        pic_name=$(basename "$pic_path")
        display_name=$(echo "$pic_name" | cut -d. -f1)
        
        # Determine the thumbnail path
        # We cache all previews to ensure consistent sizing and to handle GIFs
        thumb_path="$cache_path/${pic_name%.*}.png"

        # If it's a GIF or if we want cached thumbnails for speed
        if [[ "$pic_name" =~ \.gif$ ]]; then
            if [[ ! -f "$thumb_path" ]]; then
                # Extract first frame and resize for the Rofi icon
                magick "$pic_path"[0] -resize 480x270\! "$thumb_path"
            fi
            icon_path="$thumb_path"
        else
            # For standard images, you can use the original or cache them too
            # Using original here to save disk space, but switching to thumb_path is faster for Rofi
            icon_path="$pic_path"
        fi

        # Displaying with icon support
        printf "%s\x00icon\x1f%s\n" "$display_name" "$icon_path"
    done
}

# Choice of theme
main() {
    choice=$(menu | $rofi_command)

    # Trim any potential whitespace or hidden characters
    choice=$(echo "$choice" | xargs)
    
    if [[ -z "$choice" ]]; then
        echo "No choice selected. Exiting."
        exit 0
    fi

    # Find the index of the selected file to get the full path
    pic_index=-1
    for i in "${!PICS[@]}"; do
        filename=$(basename "${PICS[$i]}")
        # Match choice against filename (removing extension for comparison)
        if [[ "${filename%.*}" == "$choice" ]]; then
            pic_index=$i
            break
        fi
    done

    # Check if a theme was selected
    if [ "$pic_index" -ne -1 ]; then
        # Change theme & wallpaper
        # Note: 'choice' is often used as the theme name in these setups
        theme_switcher.sh "${choice}" "${PICS[$pic_index]}"
    else
        echo "No theme selected."
        exit 1
    fi
}

main