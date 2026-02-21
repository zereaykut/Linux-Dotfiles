#!/usr/bin/env bash

source $HOME/.local/share/bin/global.sh

SDDM_PATH="/usr/share/sddm/"
sddm_waydots="$SDDM_PATH/themes/SDDM-waydots/"
sddm_cache_path="/$WAYDOTS_CACHE/theme_sddm_previews/$theme/"

mkdir -p "$sddm_cache_path"

# Load theme images into array
mapfile -d '' PICS < <(find "$sddm_waydots/themes" -maxdepth 2 -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.gif" \) -print0)

# Generate thumbnails and list them for vicinae
menu() {
    # Sort the PICS array
    IFS=$'\n' sorted_options=($(sort <<<"${PICS[*]}"))

    for pic_path in "${sorted_options[@]}"; do
        pic_name=$(basename "$pic_path")

        # Standardize extension for cache (e.g., .gif -> .png)
        theme_name_raw="${pic_name%.*}"
        cached_pic="$sddm_cache_path/$theme_name_raw.png"

        # Check if the cached version already exists
        if [[ ! -f "$cached_pic" ]]; then
            # Extract first frame (for gifs) and resize
            magick "$pic_path"[0] -resize 480x270\! "$cached_pic"
        fi
        
        # Send the CACHED image path to vicinae
        echo "$cached_pic"
    done
}

# Choice of wallpapers
main() {
    # 1. Run menu to generate cache and pipe list to vicinae
    choice=$(menu | vicinae dmenu -p 'Select SDDM Theme')

    # Trim any potential whitespace
    choice=$(echo "$choice" | xargs)

    # 2. No choice case
    if [[ -z "$choice" ]]; then
        echo "No choice selected. Exiting."
        exit 0
    fi

    # 3. Process Selection
    # 'choice' is the path to the cached thumbnail (e.g., .../cache/MyTheme.png).
    # We need the theme name (e.g., "MyTheme") to find the correct config folder.
    
    selected_filename=$(basename "$choice")
    theme_name="${selected_filename%.*}" # Remove .png extension

    # 4. Apply SDDM Theme
    # The script assumes a folder exists in themes/ with the same name as the image.
    if [ -n "$theme_name" ]; then
        pkexec cp -f "$sddm_waydots/themes/$theme_name/theme.conf" "$sddm_waydots/theme.conf"
    else
        echo "No SDDM theme selected."
        exit 1
    fi
}

main