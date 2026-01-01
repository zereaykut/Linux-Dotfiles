#!/usr/bin/env bash

#------#
# INFO #
#------#

# random_kitty_gif.sh
#
# This script selects a random GIF from $HOME/.config/kitty/gifs
# and displays it in the terminal using:
#     kitty +kitten icat <gif>
#
# Requirements:
#   - kitty terminal
#   - kitty +kitten icat support
#   - GIF files stored in $HOME/.config/kitty/gifs
#
# Usage:
#   random_kitty_gif.sh
#
# The script will:
#   1. Collect all .gif files in the directory.
#   2. Randomly choose one.
#   3. Display it via kitty icat.

GIF_DIR="$HOME/.config/kitty/gifs"

# Get all .gif files in directory
mapfile -t gifs < <(find "$GIF_DIR" -maxdepth 1 -type f -name "*.gif")

# If no gifs found, exit
if [[ ${#gifs[@]} -eq 0 ]]; then
    echo "No GIFs found in $GIF_DIR"
    exit 1
fi

# Choose a random one
random_gif="${gifs[RANDOM % ${#gifs[@]}]}"

# Run the kitty icat command
kitty +kitten icat "$random_gif"