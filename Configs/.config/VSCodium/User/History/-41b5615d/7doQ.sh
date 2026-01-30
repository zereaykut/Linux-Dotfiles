#!/usr/bin/env bash

# ------------------------------------------------------------------------------
# This script generates a unified wayfire configuration file named `wayfire.ini`
# by concatenating multiple module files located in:
#   $HOME/.config/wayfire/modules
#
# The modules are combined in a fixed, predefined order to ensure deterministic
# configuration output. Each module section is prefixed with a comment header
# indicating which file it came from.
#
# Usage:
#   - Place this script in your wayfire config directory or anywhere you prefer.
#   - Run it to produce (or overwrite) `wayfire.ini` in the current directory.
#
# Notes:
#   - `wayfire.ini` will be overwritten on each run.
#   - Modify the FILES array if you add/remove module files.
# ------------------------------------------------------------------------------

MODULE_DIR="$HOME/.config/wayfire/modules"
OUTPUT_FILE="$HOME/.config/wayfire.ini"

FILES=(
  autostart.ini
  environment.ini
  animations.ini
  input_devices.ini
  keybindings.ini
  layout.ini
  misc.ini
  output_monitors.ini
  rules.ini
  theme.ini
)

# Create or empty the output file
> "$OUTPUT_FILE"

for file in "${FILES[@]}"; do
    echo "// --- $file ---" >> "$OUTPUT_FILE"
    cat "$MODULE_DIR/$file" >> "$OUTPUT_FILE"
    echo -e "\n" >> "$OUTPUT_FILE"
done

echo "Created $OUTPUT_FILE"
