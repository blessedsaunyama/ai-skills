#!/usr/bin/env bash
# Encode frames + mix -> mp4, then QA.
#   bash finish.sh "Title Of Short" [frames_dir] [suffix]
#   BEST mode: bash finish.sh "Daniel" frames_16x9 16x9   -> out/Daniel_16x9.mp4
#   FAST mode: bash finish.sh "Daniel" frames master      -> then python3 formats.py crop out/Daniel_master.mp4 9x16,16x9
set -e; T="${1:-short}"; FR="${2:-frames}"; SUF="${3:+_$3}"; mkdir -p out; F="out/${T// /-}${SUF}.mp4"; QA="out/qa_sheet${SUF}.jpg"
[ -f mix.wav ] && [ mix.wav -nt mix_raw.wav ] || ffmpeg -v error -y -i mix_raw.wav -af "loudnorm=I=-14:TP=-1.5:LRA=7" -ar 48000 -ac 2 mix.wav
ffmpeg -v error -y -framerate 30 -i "$FR/f%04d.jpg" -i mix.wav -map 0:v:0 -map 1:a:0 -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p -c:a aac -b:a 192k -shortest -movflags +faststart "$F"
ffprobe -v error -show_entries format=duration -show_entries stream=width,height,r_frame_rate -of compact "$F"
echo "--- QA (empty = no black/frozen spans)"; ffmpeg -i "$F" -vf "freezedetect=n=0.0005:d=0.4,blackdetect=d=0.05" -an -f null - 2>&1 | grep -E "freeze_start|black_start" || true
ffmpeg -i "$F" -af ebur128 -f null - 2>&1 | grep -E "^\s+I:" | tail -1
ffmpeg -v error -y -i "$F" -vf "fps=2,scale='if(gt(iw,ih),320,180)':-2,tile=8x5" -frames:v 1 "$QA"; echo "$F"
