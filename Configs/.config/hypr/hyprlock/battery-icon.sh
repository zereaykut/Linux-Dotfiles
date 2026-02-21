#!/bin/env bash

# Script to display a battery icon based on the current battery level.
# The battery level is read from the system's power supply status, and an icon is chosen based on the level (0-100%).
# If the battery is charging, it displays a charging symbol () before the battery icon.

# Read battery status and level
status=$(cat /sys/class/power_supply/BAT1/status)
level=$(cat /sys/class/power_supply/BAT1/capacity)

# Define icons for different battery levels (0-9)
icons=(
    "󰛞 󱢠 󱢠 󱢠 󱢠 "
    "󰣐 󱢠 󱢠 󱢠 󱢠 "
    "󰣐 󰛞 󱢠 󱢠 󱢠 "
    "󰣐 󰣐 󱢠 󱢠 󱢠 "
    "󰣐 󰣐 󰛞 󱢠 󱢠 "
    "󰣐 󰣐 󰣐 󱢠 󱢠 "
    "󰣐 󰣐 󰣐 󰛞 󱢠 "
    "󰣐 󰣐 󰣐 󰣐 󱢠 "
    "󰣐 󰣐 󰣐 󰣐 󰛞 "
    "󰣐 󰣐 󰣐 󰣐 󰣐 "
)

# Determine the appropriate icon index
i=$((level / 10))
[[ "$i" -gt 9 ]] && i=9

# Output charging symbol if charging
[[ "$status" == "Charging" ]] && printf " "

# Output the battery icon
printf "%s\n" "${icons[$i]}"

