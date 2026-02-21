#!/usr/bin/env bash

source $HOME/.local/share/bin/global.sh

themes_path="$WAYDOTS_PATH/themes/"
theme_cache_path="/$WAYDOTS_CACHE/theme_previews/$theme/"

mkdir -p "$theme_cache_path"

# Load original images into an array
mapfile -d '' PICS < <(find "$themes_path" -maxdepth 2 -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.gif" \) -print0)

# Generate thumbnails and list them for vicinae
menu() {
    # Sort the PICS array
    IFS=$'\n' sorted_options=($(sort <<<"${PICS[*]}"))

    for pic_path in "${sorted_options[@]}"; do
        pic_name=$(basename "$pic_path")
        
        # specific handling to clean extensions for the cache filename
        # e.g., "image.jpg" -> "image.png" and "animation.gif" -> "animation.png"
        theme_name_raw="${pic_name%.*}"
        cached_pic="$theme_cache_path/$theme_name_raw.png"

        # Check if the cached version already exists
        if [[ ! -f "$cached_pic" ]]; then
            # Extract first frame (for gifs) and resize
            magick "$pic_path"[0] -resize 480x270\! "$cached_pic"
        fi
        
        # Send the CACHED image path to vicinae
        # Vicinae will display this small, fast-loading image
        echo "$cached_pic"
    done
}

main() {
    # 1. Run menu to generate cache and pipe list to vicinae
    choice=$(menu | vicinae dmenu -p 'Select Theme')

    # Trim any potential whitespace
    choice=$(echo "$choice" | xargs)

    # 2. No choice case
    if [[ -z "$choice" ]]; then
        echo "No choice selected. Exiting."
        exit 0
    fi

    # 3. Resolve the Original File
    # 'choice' is currently the path to the cached thumbnail (e.g., .../cache/mytheme.png).
    # We need to find the original file (e.g., .../themes/mytheme.jpg).
    
    selected_filename=$(basename "$choice")
    selected_theme_name="${selected_filename%.*}" # Remove .png extension

    original_file=""
    
    # Loop through original PICS to find the matching theme name
    for pic in "${PICS[@]}"; do
        # Get basename without extension of the original picture
        base_name=$(basename "$pic")
        base_name_no_ext="${base_name%.*}"
        
        if [[ "$base_name_no_ext" == "$selected_theme_name" ]]; then
            original_file="$pic"
            break
        fi
    done

    # 4. Apply the theme
    if [ -n "$original_file" ]; then
        theme-switcher.sh "$selected_theme_name" "$original_file"
    else
        echo "Error: Could not locate original file for theme '$selected_theme_name'."
        exit 1
    fi
}

main