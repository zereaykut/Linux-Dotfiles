#!/bin/env bash

# This script lists all executable .sh files in the ~/.local/share/bin directory, 
# displays them in a rofi menu for the user to select, and then executes the 
# selected script. If no scripts are found, it exits with an error message.

# List all executable bash scripts in the target directory, show only the filenames
scripts=$(find ~/.local/share/bin -maxdepth 1 -type f -executable | sort | xargs -n 1 basename)

# If there are no scripts, exit
if [ -z "$scripts" ]; then
    echo "No scripts found!"
    exit 1
fi

# Use rofi to display the scripts (only the filenames)
selected_script=$(echo "$scripts" | rofi -dmenu -i -p "Select script:")

# If user selected something, execute it
if [ -n "$selected_script" ]; then
    # Get the full path to the selected script
    full_script=$(find ~/.local/share/bin -maxdepth 1 -type f -executable -name "$selected_script")
    
    # Execute the selected script
    "$full_script"
fi
