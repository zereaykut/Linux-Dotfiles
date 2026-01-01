#!/usr/bin/env bash

# Directory to save screenshots
DIR="$HOME/Pictures/Screenshots"
mkdir -p "$DIR"

# Timestamp for filenames
TS="$(date +'%Y-%m-%d_%H-%M-%S')"

usage() {
    echo "Usage: $0 [region|full|edit-region|edit-full]"
    exit 1
}

case "$1" in
    region)
        grim -g "$(slurp)" "$DIR/screenshot-$TS.png"
        ;;

    full)
        grim "$DIR/screenshot-$TS.png"
        ;;

    edit-region)
        grim -g "$(slurp)" - | swappy -f -
        ;;

    edit-full)
        grim - | swappy -f -
        ;;

    *)
        usage
        ;;
esac

echo "Saved: $DIR/screenshot-$TS.png"
