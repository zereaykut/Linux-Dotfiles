#!/usr/bin/env bash

source "$HOME/.local/share/bin/global.sh"
source "$WAYDOTS_CACHE/theme.sh"

wall_path="$WAYDOTS_PATH/themes/$theme/wallpapers/"
wall_cache_path="$WAYDOTS_CACHE/wallpaper_previews/$theme/"

mkdir -p "$wall_cache_path"

# Retrieve image files using null delimiter to handle spaces in filenames
mapfile -d '' PICS < <(find "$wall_path" -type f \( -iname "*.jpg" -o -iname "*.jpeg" -o -iname "*.png" -o -iname "*.gif" \) -print0)

# Sorting and caching wallpapers
menu() {
    # Sort the PICS array
    IFS=$'\n' sorted_options=($(sort <<<"${PICS[*]}"))
    
    for pic_path in "${sorted_options[@]}"; do
        pic_name=$(basename "$pic_path")

        # Standardize cache filenames (remove original extension, add .png)
        # This handles jpg, png, and gif uniformly.
        base_name="${pic_name%.*}"
        cached_pic="$wall_cache_path/$base_name.png"
            
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
    # 1. Run menu and pipe to vicinae
    choice=$(menu | vicinae dmenu -p 'Select Wallpaper')
  
    # Trim whitespace
    choice=$(echo "$choice" | xargs)

    # 2. No choice case
    if [[ -z "$choice" ]]; then
        echo "No choice selected. Exiting."
        exit 0
    fi

    # 3. Resolve Original File
    # 'choice' is the path to the cached thumbnail (e.g. .../cache/wall1.png)
    # We need to find the original (e.g. .../wallpapers/wall1.jpg)
    
    selected_filename=$(basename "$choice")
    selected_base="${selected_filename%.*}" # Remove .png

    original_file=""
    
    for pic in "${PICS[@]}"; do
        p_name=$(basename "$pic")
        p_base="${p_name%.*}"
        
        # Compare filenames without extensions
        if [[ "$p_base" == "$selected_base" ]]; then
            original_file="$pic"
            break
        fi
    done

    # 4. Execute Switcher
    if [ -n "$original_file" ]; then
        # Change wallpaper using sww
        wall-switcher.sh "$original_file"
        theme-lock-cache.sh "$original_file"
    else
        echo "Error: Could not locate original file for wallpaper '$selected_base'."
        exit 1
    fi
}

main