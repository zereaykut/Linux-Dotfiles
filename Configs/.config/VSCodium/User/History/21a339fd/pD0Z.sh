#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(dirname "$(realpath "$0")")
TARGET_DIR="$SCRIPT_DIR/../Move/pacman"

if [ -d "$TARGET_DIR" ]; then
    cd "$TARGET_DIR"
    echo "📂 Now in directory: $(pwd)"
else
    echo "❌ Directory does not exist: $TARGET_DIR"
    exit 1
fi
