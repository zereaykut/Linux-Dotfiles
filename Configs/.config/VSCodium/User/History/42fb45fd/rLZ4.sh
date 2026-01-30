#!/usr/bin/env bash
#
# launch_polkit_agent.sh
#
# Starts a Polkit authentication agent if none is running.
# Required for privilege prompts in Wayland / minimal desktop setups
# (Hyprland, Sway, etc.), where no agent is started automatically.
#
# Usage:
#   Run once per session (e.g. from compositor config)
#

set -e

# Exit if a polkit agent is already running
if pgrep -f "polkit-.*-agent" >/dev/null; then
    exit 0
fi

# Known polkit agent locations
AGENTS=(
    "/usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1"
    "/usr/libexec/polkit-gnome-authentication-agent-1"
    "/usr/lib/polkit-kde-authentication-agent-1"
    "/usr/libexec/polkit-kde-authentication-agent-1"
    "/usr/lib/lxqt-policykit/lxqt-policykit-agent"
    "/usr/libexec/lxqt-policykit-agent"
    "/usr/lib/mate-polkit/polkit-mate-authentication-agent-1"
    "/usr/libexec/polkit-mate-authentication-agent-1"
)

for agent in "${AGENTS[@]}"; do
    if [ -x "$agent" ]; then
        "$agent" &
        disown
        exit 0
    fi
done

# Fallback: search in PATH
for cmd in \
    polkit-gnome-authentication-agent-1 \
    polkit-kde-authentication-agent-1 \
    lxqt-policykit-agent \
    polkit-mate-authentication-agent-1
do
    if command -v "$cmd" >/dev/null 2>&1; then
        "$cmd" &
        disown
        exit 0
    fi
done

echo "No polkit authentication agent found." >&2
exit 1

