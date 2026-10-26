#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
ffmpeg -v error -y -i original_score_and_foley.wav -af loudnorm=I=-16:TP=-1.5:LRA=9 -ar 48000 -c:a pcm_s16le master_audio.wav
ffmpeg -hide_banner -y -framerate 12 -pattern_type glob -i 'frames/*.png' -i master_audio.wav -vf 'tpad=stop_mode=clone:stop_duration=0.25,minterpolate=fps=24:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1,scale=720:1280:flags=lanczos,setsar=1,format=yuv420p' -t 70 -c:v libx264 -threads 5 -preset slow -crf 18 -c:a aac -b:a 192k -ar 48000 -movflags +faststart -color_primaries bt709 -color_trc bt709 -colorspace bt709 -metadata title='Marble Workshop - One Little Chain' -metadata comment='Original CGI miniature, original music and procedural foley. 540x960 12fps source, denoised, motion-interpolated to 24fps and upscaled to 720x1280. Rigid-body domino replay and staged mechanisms; not live-action footage.' workshop_chain_70s.mp4
