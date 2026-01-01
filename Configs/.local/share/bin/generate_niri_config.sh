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
CONFIG_DIR="$HOME/.config/niri/config.kdl"

FILES=(
  autostart.kdl
  environment.kdl
  input.kdl
  output.kdl
  animations.kdl
  gestures.kdl
  keybindings.kdl
  misc.kdl
  rules.kdl
  theme.kdl
)

# Create or empty the output file
> "$CONFIG_DIR"

for file in "${FILES[@]}"; do
    echo "// --- $file ---" >> "$CONFIG_DIR"
    cat "$MODULE_DIR/$file" >> "$CONFIG_DIR"
    echo -e "\n" >> "$CONFIG_DIR"
done

echo "Created $CONFIG_DIR"
