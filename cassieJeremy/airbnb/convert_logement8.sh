#!/bin/bash
cd /Users/gregoirecollin/Documents/code/stalkie-assets/cassieJeremy/airbnb/logement_8

index=1
for avif_file in *.avif; do
  if [ -f "$avif_file" ]; then
    ffmpeg -i "$avif_file" -q:v 85 "photo_${index}.webp" -y > /dev/null 2>&1
    if [ -f "photo_${index}.webp" ]; then
      echo "Converti: $avif_file -> photo_${index}.webp"
      rm "$avif_file"
      index=$((index + 1))
    fi
  fi
done

echo "✓ Conversion terminée pour logement_8!"
