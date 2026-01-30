#!/usr/bin/env bash

# This script provides a simple menu interface for managing a NetBird VPN connection
# using Rofi. It allows the user to:
# - Connect to the VPN (`netbird up`)
# - Disconnect from the VPN (`netbird down`)
# - Check the VPN status (`netbird status`)
# - Add a new connection using a setup key (`netbird up --setup-key <key>`)
# - Exit the script

# The script displays a menu with these options using Rofi and executes the appropriate
# NetBird command based on the user's selection.

# Define the menu options for Rofi
options="Connect\nDisconnect\nStatus\nAdd Connection\nExit"

# Display Rofi menu and capture the selected option
selected=$(echo -e "$options" | rofi -dmenu -theme-str 'entry {placeholder:"Netbird VPN";}')

# Handle each selected option
case "$selected" in
    "Connect")
        # Run "netbird up" to connect
        netbird up
        ;;
    "Disconnect")
        # Run "netbird down" to disconnect
        netbird down
        ;;
    "Status")
        # Run "netbird status" and display the output in Rofi
        status_output=$(netbird status)
        echo "$status_output" | rofi -dmenu -p "NetBird Status:"
        ;;
    "Add Connection")
        # Ask for the setup key
        setup_key=$(rofi -dmenu -p "Enter Setup Key:")
        
        if [[ -n "$setup_key" ]]; then
            # Run "netbird up --setup-key {setup_key}" to add a connection
            netbird up --setup-key "$setup_key"
        else
            # Handle case where no setup key is entered
            rofi -e "No setup key entered."
        fi
        ;;
    "Exit")
        # Exit the script
        exit 0
        ;;
    *)
        # If no valid selection, exit
        exit 1
        ;;
esac
