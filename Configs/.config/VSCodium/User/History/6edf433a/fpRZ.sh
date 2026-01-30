#!/usr/bin/env bash
# System - Scripts
export SOURCE_PATH="$HOME/.local/share/bin"
export CACHE_PATH="$HOME/.cache"
export CONFIG_PATH="$HOME/.config"
export WAYDOTS_PATH="$CONFIG_PATH/waydots"

# Theming
export ICONS_PATH="$HOME/.icons"
export THEMES_PATH="$HOME/.themes"

# WM & Desktop
export HYPR_CONFIG_PATH="$CONFIG_PATH/hypr"
export NIRI_CONFIG_PATH="$CONFIG_PATH/niri"

export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
export XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$HOME/.cache}"
export XDG_STATE_HOME="${XDG_STATE_HOME:-$HOME/.local/state}"