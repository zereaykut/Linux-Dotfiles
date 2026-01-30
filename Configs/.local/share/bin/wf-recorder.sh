#!/usr/bin/env bash

source $HOME/.local/share/bin/global.sh

# Define the directory where recordings will be saved
recording_dir="$HOME/Videos/wf-recorder"

# Define cache directory & file
cache_dir="$CACHE_PATH/wf-recorder"
mkdir -p "$cache_dir"
touch "$cache_dir/wf-recorder.log"

record() {
    # Start recording
    local filename="$recording_dir/wf-recorder-$(date +'%Y-%m-%d-%H-%M-%S').mp4" --app-name="wf-recorder" --icon="wf-recorder"
    notify-send "Video recording started with wf-recorder 📹" -u normal
    echo "<NOTICE> $(date +"%Y-%m-%d %H:%M:%S"): Video recording started with wf-recorder - $filename" >> $cache_dir/wf-recorder.log
    
    wf-recorder -a --file "$filename"
}

# Function to handle recording start or stop
record_or_stop() {
    # Check if the recording directory exists; create it if not
    if [[ ! -d $recording_dir ]]; then
        mkdir -p "$recording_dir" || { echo "Error: Failed to create the directory $recording_dir"; exit 1; }
    fi

    # Check if recording should start or stop
    if ! pgrep -x "wf-recorder" > /dev/null; then
        record
        
    else
        # Stop recording
        local pid
        pid=$(pidof wf-recorder)

        if [[ -n $pid ]]; then
            # Send SIGINT signal to stop wf-recorder
            echo "Sending Ctrl + C signal to wf-recorder with PID $pid"
            kill -SIGINT "$pid"

            # Get the most recent recording file
            local filename
            filename=$(ls -t "$recording_dir" | head -n1) --app-name="wf-recorder" --icon="wf-recorder"
            echo "Video recording ended and saved to $filename"
            notify-send "Video recording ended and saved to: $recording_dir/$filename 📹" -u normal
            echo "<NOTICE> $(date +"%Y-%m-%d %H:%M:%S"): Video recording ended and saved to: $recording_dir/$filename - wf-recorder" >> $cache_dir/wf-recorder.log
        else
            echo "wf-recorder is not running."
            echo "<NOTICE> $(date +"%Y-%m-%d %H:%M:%S"): wf-recorder is not running - wf-recorder" >> $cache_dir/wf-recorder.log
        fi
    fi
}

# Call the function to start or stop recording


# Launch wf-recorder
case $1 in
    region)
        echo "not implemented"
        ;;
    swaync)
        if [[ $SWAYNC_TOGGLE_STATE == true ]]; then
            record_or_stop 
        fi
        ;;
    *)
        record_or_stop 
        ;;
esac