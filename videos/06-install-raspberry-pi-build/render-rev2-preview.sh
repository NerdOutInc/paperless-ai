#!/usr/bin/env bash
set -euo pipefail

SRC_VIDEO="videos/src/06-install-raspberry-pi.mp4"
SRC_AUDIO="videos/src/06-install-raspberry-pi.m4a"
INTRO_CLIP="videos/06-install-raspberry-pi-build/hyperframes-rpi-slides/clips/rpi-intro-hyperframes.mp4"
SD_CLIP="videos/06-install-raspberry-pi-build/hyperframes-rpi-slides/clips/rpi-sd-insert-hyperframes.mp4"
OUT="videos/06-install-raspberry-pi-build/renders/06-install-raspberry-pi-rev2-preview.mp4"

FILTER='
[1:v]trim=start=0:end=30,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p[v0];
[0:v]trim=start=4:end=4.5,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=9.42[v1];
[0:v]trim=start=4.5:end=20.5,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=17.38[v2];
[0:v]trim=start=20.5:end=24,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=5.0[v3];
[0:v]trim=start=24:end=28.2,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p[v4];
[0:v]trim=start=28.2:end=47.5,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=3.2[v5];
[0:v]trim=start=47.5:end=59,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=8.84[v6];
[0:v]trim=start=59:end=62,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=4.16[v7];
[0:v]trim=start=62:end=66,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=5.0[v8];
[0:v]trim=start=66:end=74,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=2.0[v9];
[2:v]trim=start=0:end=10,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p[v10];
[0:v]trim=start=79:end=79.5,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=2.0[v11];
[0:v]trim=start=79.5:end=88.5,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=24.5[v12];
[0:v]trim=start=96:end=116,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=5.58[v13];
[0:v]trim=start=116:end=121.5,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=15.58[v14];
[0:v]trim=start=121.5:end=132,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=16.66[v15];
[0:v]trim=start=132:end=132.5,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=6.96[v16];
[0:v]trim=start=132.5:end=138.5,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=18.0[v17];
[0:v]trim=start=138.5:end=142.5,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=0.22[v18];
[0:v]trim=start=142.5:end=151,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p[v19];
[0:v]trim=start=151:end=156.5,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=15.14[v20];
[0:v]trim=start=156.5:end=166.5,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=25.88[v21];
[0:v]trim=start=166.5:end=181.5,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=15.480975[v22];
[0:v]trim=start=181.5:end=184.216667,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p[v23];
[v0][v1][v2][v3][v4][v5][v6][v7][v8][v9][v10][v11][v12][v13][v14][v15][v16][v17][v18][v19][v20][v21][v22][v23]concat=n=24:v=1:a=0[vout]
'

cmd=(
  ffmpeg
  -y
  -i "$SRC_VIDEO"
  -i "$INTRO_CLIP"
  -i "$SD_CLIP"
  -i "$SRC_AUDIO"
  -filter_complex "$FILTER"
  -map "[vout]"
  -map "3:a"
  -c:v libx264
  -preset veryfast
  -crf 24
  -pix_fmt yuv420p
  -c:a aac
  -b:a 128k
  -movflags +faststart
  -shortest
  "$OUT"
)

printf 'FFmpeg command before render:\n'
printf '%q ' "${cmd[@]}"
printf '\n'

"${cmd[@]}"
