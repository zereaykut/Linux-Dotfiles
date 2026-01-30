#!/bin/env bash

# Function to create .cbr (RAR format) or .cbz (ZIP format)
compress_folder() {
  folder_path="$1"
  folder_name=$(basename "$folder_path")
  output_format="$2"
  
  # Change to the folder
  cd "$folder_path" || exit

  # Collect all image files (you can add more extensions if needed)
  image_files=($(find . -type f \( -iname "*.png" -o -iname "*.jpg" -o -iname "*.jpeg" \)))

  if [ "${#image_files[@]}" -eq 0 ]; then
    echo "No image files found in '$folder_name'. Skipping."
    return
  fi

  # Compress into the chosen format
  case "$output_format" in
    cbr)
      # Create a .cbr (using rar)
      rar a -ep1 "../$folder_name.cbr" "${image_files[@]}"
      ;;
    cbz)
      # Create a .cbz (using zip)
      zip -r "../$folder_name.cbz" "${image_files[@]}"
      ;;
    *)
      echo "Unsupported format: $output_format"
      return
      ;;
  esac

  # Go back to the original directory
  cd - > /dev/null
  echo "Compressed $folder_name into $folder_name.$output_format"
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

# Main execution
for folder in "$main_folder"/*/; do
  # Ensure we are processing directories
  if [ -d "$folder" ]; then
    # Ask the user for the desired format for each folder (cbr or cbz)
    echo "Do you want to compress the folder '$folder' into .cbr or .cbz?"
    read -p "Enter format (cbr/cbz): " format_choice

    # Compress the folder based on user input
    if [[ "$format_choice" =~ ^(cbr|cbz)$ ]]; then
      compress_folder "$folder" "$format_choice"
    else
      echo "Invalid format. Skipping '$folder'."
    fi
  fi
done
