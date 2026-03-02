#!/usr/bin/env bash

style="${1:-1}"
rofi_theme="$HOME/.config/rofi/launchers/launcher_$style.rasi"

## Run
rofi -show drun -theme $rofi_theme
