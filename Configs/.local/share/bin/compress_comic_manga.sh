#!/bin/env bash

# This script compresses image files (.png, .jpg, .jpeg) inside subfolders of a given directory 
# into .cbz files (which are essentially ZIP archives). It scans each subfolder, collects image files,
# and creates a .cbz archive for each subfolder containing those images.

# Usage:
# ./compress_images_to_cbz.sh <main_folder>
# Where <main_folder> is the path to the folder that contains subfolders with image files you want to compress.
#
# Example:
# ./compress_images_to_cbz.sh /path/to/parent_folder
#
# This will create .cbz files for each subfolder containing images inside '/path/to/parent_folder'.


# Function to create .cbz (ZIP format)
compress_folder() {
  folder_path="$1"
  folder_name=$(basename "$folder_path")
  
  # Change to the folder
  cd "$folder_path" || exit

  # Collect all image files (you can add more extensions if needed)
  image_files=($(find . -type f \( -iname "*.png" -o -iname "*.jpg" -o -iname "*.jpeg" \)))

  if [ "${#image_files[@]}" -eq 0 ]; then
    echo "No image files found in '$folder_name'. Skipping."
    return
  fi

  # Compress into the .cbz (using zip)
  zip -r "../$folder_name.cbz" "${image_files[@]}"

  # Go back to the original directory
  cd - > /dev/null
  echo "Compressed $folder_name into $folder_name.cbz"
}

# Check if a directory parameter was provided
if [ -z "$1" ]; then
  echo "Usage: $0 <main_folder>"
  exit 1
fi

main_folder="$1"

# Ensure the main folder exists
if [ ! -d "$main_folder" ]; then
  echo "Error: '$main_folder' is not a valid directory."
  exit 1
fi

# Main execution: Loop through all subfolders in the provided main folder
for folder in "$main_folder"/*/; do
  # Ensure we are processing directories
  if [ -d "$folder" ]; then
    compress_folder "$folder"
  fi
done

echo "Compression completed!"
