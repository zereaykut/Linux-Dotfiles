#!/usr/bin/env bash
export SOURCE_PATH="$HOME/.local/share/bin"
export CACHE_PATH="$HOME/.cache"

export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$HOME/.config}"
export XDG_DATA_HOME="${XDG_DATA_HOME:-$HOME/.local/share}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-$HOME/.cache}"
export XDG_STATE_HOME="${XDG_STATE_HOME:-$HOME/.local/state}"
export XDG_HYPR_CONFIG="${XDG_HYPR_CONFIG:-$XDG_CONFIG_HOME/hypr}"
export XDG_NIRI_CONFIG="${XDG_HYPR_CONFIG:-$XDG_CONFIG_HOME/niri}"
export ICONS_DIR="$XDG_DATA_HOME/icons"
export FONTS_DIR="$XDG_DATA_HOME/fonts"
export THEMES_DIR="$XDG_DATA_HOME/themes"