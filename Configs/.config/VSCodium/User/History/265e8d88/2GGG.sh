#!/usr/bin/env bash

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