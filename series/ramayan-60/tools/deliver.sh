#!/bin/bash
# Compressed share copies of every finished episode in delivery/ (about 15 MB each, 1080x1920)
cd "$(dirname "$0")/.."
for f in ep*/out/Ramayan_Ep*.mp4; do
  o=delivery/$(basename "$f")
  [ -f "$o" ] && [ "$o" -nt "$f" ] && continue
  ffmpeg -loglevel error -y -i "$f" -c:v libx264 -preset slow -crf 24 -maxrate 2200k -bufsize 4400k -pix_fmt yuv420p -c:a aac -b:a 128k -movflags +faststart "$o" && echo "$o $(du -h "$o" | cut -f1)"
done
cp social/Ramayan_60_Captions.pdf social/captions.txt delivery/
