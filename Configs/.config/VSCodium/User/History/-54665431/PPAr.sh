#!/bin/env bash

# Define your wallpapers directory
source $HOME/.cache/waydots/theme.sh
wall_path="$HOME/.config/waydots/themes/$theme/wallpapers/"
rofi_conf="$HOME/.config/rofi/wallpaper_select.rasi"
cache_path="/$HOME/.cache/waydots/$theme/"
mkdir -p $cache_path

# Retrieve image files using null delimiter to handle spaces in filenames
mapfile -d '' PICS < <(find "$wall_path" -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.gif" \) -print0)

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
            cached_pic="$cache_path/$(basename "$pic_path" .gif).png"
            
            # Check if the cached version already exists
            if [[ ! -f "$cached_pic" ]]; then
                # echo "Creating cached first frame for GIF: $pic_name"
                # Extract first frame if it doesn't exist
                magick "$pic_path"[0] -resize 480x270\! "$cached_pic"
            fi
            pic_path="$cached_pic"  # Replace GIF with cached first frame PNG
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
        # Change wallpaper using sww
        wall_switcher.sh "${PICS[$pic_index]}"
        theme_lock_cache.sh "${PICS[$pic_index]}"
    else
        echo "No wallpaper selected."
        exit 1
    fi
}

main
