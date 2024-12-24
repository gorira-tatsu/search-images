#!/bin/bash

IMAGE_DIR="/Users/tatsujin/code/hos/Pictures/2024-08-27"

SERVER_URL="http://100.107.92.46:8100/lifelog/save_image/"

for image in "$IMAGE_DIR"/*.{jpg,jpeg,png}; do
  if [[ -f "$image" ]]; then
    echo "Uploading $image..."
    curl -X 'POST' \
      "$SERVER_URL" \
      -H 'accept: application/json' \
      -H 'Content-Type: multipart/form-data' \
      -F "file=@$image;type=$(file --mime-type -b "$image")"
    echo -e "\nFinished uploading $image"
  else
    echo "No valid image files found in $IMAGE_DIR"
  fi
done
