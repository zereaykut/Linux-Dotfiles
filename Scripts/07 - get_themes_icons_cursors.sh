#!/usr/bin/env bash

set -e

mkdir -p ~/.themes ~/.icons
sudo mkdir -p /usr/share/themes /usr/share/icons

srcGtk="../Source/Gtk"
for file in $srcGtk/*.tar.gz; do
  tar -xvzf "$file" -C ~/.themes/
  sudo tar -xvzf "$file" -C /usr/share/themes
done

srcIcon="../Source/Icon"
for file in $srcIcon/*.tar.gz; do
  tar -xvzf "$file" -C ~/.icons
  sudo tar -xvzf "$file" -C /usr/share/icons
done

srcCursor="../Source/Cursor"
for file in $srcCursor/*.tar.gz; do
  tar -xvzf "$file" -C ~/.icons
  sudo tar -xvzf "$file" -C /usr/share/icons
done
