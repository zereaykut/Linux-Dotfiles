#!/bin/env bash

CACHE_PATH="$HOME/.cache/waydots"

source $CACHE_PATH/theme.sh
source $CACHE_PATH/wall_select.sh

theme_switcher.sh "$theme" "$wall_select"