#!/usr/bin/env bash

# ------------------------------------------------------------------------------
# This script generates a unified Niri configuration file named `config.kdl`
# by concatenating multiple module files located in:
#   $HOME/.config/niri/modules
#
# The modules are combined in a fixed, predefined order to ensure deterministic
# configuration output. Each module section is prefixed with a comment header
# indicating which file it came from.
#
# Usage:
#   - Place this script in your Niri config directory or anywhere you prefer.
#   - Run it to produce (or overwrite) `config.kdl` in the current directory.
#
# Notes:
#   - `config.kdl` will be overwritten on each run.
#   - Modify the FILES array if you add/remove module files.
# ------------------------------------------------------------------------------

MODULE_DIR="$HOME/.config/niri/modules"
OUTPUT_FILE="config.kdl"

FILES=(
  animations.kdl
  autostart.kdl
  gestures.kdl
  input.kdl
  keybindings.kdl
  layout.kdl
  misc.kdl
  environment.kdl
  output.kdl
  rules.kdl
  theme.kdl
)

# Create or empty the output file
> "$OUTPUT_FILE"

for file in "${FILES[@]}"; do
    echo "// --- $file ---" >> "$OUTPUT_FILE"
    cat "$MODULE_DIR/$file" >> "$OUTPUT_FILE"
    echo -e "\n" >> "$OUTPUT_FILE"
done

echo "Created $OUTPUT_FILE"
