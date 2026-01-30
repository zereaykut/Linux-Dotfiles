#!/usr/bin/env bash

source $HOME/.local/share/bin/global.sh

# Input file (could be any image file path)
wall_path="$1"
wall_cache_path="$WAYDOTS_CACHE/themes"

mkdir -p $wall_cache_path

# Check if the input file exists
if [ ! -f "$wall_path" ]; then
    echo "File does not exist!"
    exit 1
fi

# Get the file extension
fileExtension="${wall_path##*.}"

# Check if ImageMagick is installed with 'convert' or 'magick'
if command -v convert &> /dev/null; then
    command="convert"
elif command -v magick &> /dev/null; then
    command="magick"
else
    echo "Neither 'convert' nor 'magick' command found. Please install ImageMagick."
    exit 1
fi

# Check if the file is already a PNG
if [ "${fileExtension,,}" == "png" ]; then
    # If it's a PNG, just copy it to the .cache/themes folder
    cp "$wall_path" "$wall_cache_path/lock_screen.png"
    echo "PNG image copied to $wall_cache_path/lock_screen.png"
else
    # Otherwise, convert the image to PNG using ImageMagick and copy it to the folder
    $command "$wall_path[0]" "$wall_cache_path/lock_screen.png"
    echo "Image converted to PNG and copied to $wall_cache_path"
fi
