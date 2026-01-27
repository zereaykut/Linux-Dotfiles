#!/usr/bin/env bash

current_profile=$(powerprofilesctl get)


case "$current_profile" in
    "performance")
        text=""
        tooltip=" Performance"
        echo "{\"text\":\"$text\", \"tooltip\":\"$tooltip\"}"
        ;;
    "balanced")
        text=""
        tooltip=" Balanced"
        echo "{\"text\":\"$text\", \"tooltip\":\"$tooltip\"}"
        ;;
    "power-saver")
        text=""
        tooltip=" Power-Saver"
        echo "{\"text\":\"$text\", \"tooltip\":\"$tooltip\"}"
        ;;
    *)
        echo "Unknown power profile: $current_profile"
        ;;
esac
