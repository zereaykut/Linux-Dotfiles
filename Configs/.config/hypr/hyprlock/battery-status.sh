#!/bin/env bash

# Get the battery status from the system
status=$(cat /sys/class/power_supply/BAT1/status)
level=$(cat /sys/class/power_supply/BAT1/capacity)

# Find the battery device using upower
bat=$(upower -e | grep BAT)

# Check battery status and display the appropriate information
if [[ "$status" == "Discharging" && "$level" -ne 100 ]]; then
    echo -n "Time to empty: "
    upower -i "$bat" | grep "time to empty" | awk -F': ' '{print $2}'
elif [[ "$status" == "Charging" && "$level" -ne 100 ]]; then
    echo -n "Time to full: "
    upower -i "$bat" | grep "time to full" | awk -F': ' '{print $2}'
elif [[ "$level" -eq 100 ]]; then
    echo "Full"
else
    echo "Battery status: $status"
fi
