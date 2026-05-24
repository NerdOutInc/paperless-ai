#!/usr/bin/env bash
set -euo pipefail

SRC_VIDEO="videos/src/06-install-raspberry-pi.mp4"
SRC_AUDIO="videos/src/06-install-raspberry-pi.m4a"
INTRO_CLIP="videos/06-install-raspberry-pi-build/hyperframes-rpi-slides/clips/rpi-intro-hyperframes-rev4.mp4"
SD_CLIP="videos/06-install-raspberry-pi-build/hyperframes-rpi-slides/clips/rpi-sd-insert-hyperframes-rev4.mp4"
INDEXING_CLIP="videos/src/06-install-raspberry-pi-indexing-normal-speed.mp4"
RECAP_CLIP="videos/06-install-raspberry-pi-build/hyperframes-rpi-slides/clips/rpi-recap-hyperframes-rev5.mp4"
OUT="videos/06-install-raspberry-pi-build/renders/06-install-raspberry-pi-final-hq.mp4"

FILTER='
[1:v]trim=start=0:end=31,setpts=PTS-STARTPTS,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p,settb=AVTB[intro];
[0:v]trim=start=4:end=4.5,setpts=PTS-STARTPTS,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=9.42[b0];
[0:v]trim=start=4.5:end=20.5,setpts=PTS-STARTPTS,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=17.38[b1];
[0:v]trim=start=20.5:end=24,setpts=PTS-STARTPTS,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=5.0[b2];
[0:v]trim=start=24:end=28.2,setpts=PTS-STARTPTS,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p[b3];
[0:v]trim=start=28.2:end=30.0,setpts=PTS-STARTPTS,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=1.2[b4];
[0:v]trim=start=30.2:end=33.2,setpts=(PTS-STARTPTS)*0.6666666667,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p[b5];
[0:v]trim=start=33.2:end=36.2,setpts=(PTS-STARTPTS)*0.4166666667,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p[b6];
[0:v]trim=start=36.2:end=41.2,setpts=(PTS-STARTPTS)*0.58,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p[b7];
[0:v]trim=start=41.2:end=43.2,setpts=(PTS-STARTPTS)*0.625,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p[b8];
[0:v]trim=start=43.2:end=47.5,setpts=(PTS-STARTPTS)*0.6046511628,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p[b9];
[0:v]trim=start=47.5:end=47.516667,setpts=PTS-STARTPTS,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=9.483333[b10];
[0:v]trim=start=48:end=59,setpts=PTS-STARTPTS,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=9.34[b11];
[0:v]trim=start=59:end=62,setpts=PTS-STARTPTS,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=4.16[b12];
[0:v]trim=start=62:end=74,setpts=(PTS-STARTPTS)*1.5833333333,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p[b13];
[2:v]trim=start=0:end=10,setpts=PTS-STARTPTS,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p,fade=t=in:st=0:d=0.75:color=white,fade=t=out:st=9.25:d=0.75:color=black[b14];
[0:v]trim=start=79:end=81,setpts=(PTS-STARTPTS)*2.0,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p[b15];
[0:v]trim=start=81.45:end=81.466667,setpts=PTS-STARTPTS,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=13.983333[b16];
[0:v]trim=start=81.45:end=82,setpts=PTS-STARTPTS,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p[b17];
[0:v]trim=start=82:end=82.016667,setpts=PTS-STARTPTS,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=7.433333[b18];
[0:v]trim=start=82:end=85,setpts=(PTS-STARTPTS)*0.3333333333,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p[b19];
[0:v]trim=start=85:end=85.016667,setpts=PTS-STARTPTS,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=9.983333[b20];
[0:v]trim=start=85:end=99.65,setpts=(PTS-STARTPTS)*0.614334471,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p[b21];
[0:v]trim=start=99.65:end=99.666667,setpts=PTS-STARTPTS,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=10.983333[b22];
[0:v]trim=start=99.65:end=110.35,setpts=(PTS-STARTPTS)*0.2803738318,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p[b23];
[0:v]trim=start=110.35:end=121.5,setpts=(PTS-STARTPTS)*2.0322869955,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p[b24];
[0:v]trim=start=121.5:end=132,setpts=PTS-STARTPTS,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=16.66[b25];
[0:v]trim=start=132:end=132.5,setpts=PTS-STARTPTS,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=6.96[b26];
[0:v]trim=start=132.5:end=136,setpts=PTS-STARTPTS,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p[b27a];
[0:v]trim=start=136:end=136.016667,setpts=PTS-STARTPTS,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=3.203333[b27b];
[0:v]trim=start=136:end=145,setpts=PTS-STARTPTS,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p[b28a];
[3:v]trim=start=0:end=12,setpts=PTS-STARTPTS,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p[b28b];
[0:v]trim=start=145:end=152,setpts=PTS-STARTPTS,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p[b28c1];
[0:v]trim=start=152:end=152.016667,setpts=PTS-STARTPTS,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=8.983333[b28h];
[0:v]trim=start=152:end=164,setpts=PTS-STARTPTS,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p[b28c2];
[0:v]trim=start=164:end=164.016667,setpts=PTS-STARTPTS,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=16.983333[b31];
[0:v]trim=start=164:end=168,setpts=PTS-STARTPTS,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p[b32];
[0:v]trim=start=168:end=180,setpts=(PTS-STARTPTS)*1.4166666667,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p[b34];
[0:v]trim=start=180:end=180.016667,setpts=PTS-STARTPTS,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=13.983333[b35];
[4:v]trim=start=0.5:end=16.5,setpts=PTS-STARTPTS,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p[b35r];
[0:v]trim=start=181.5:end=184.216667,setpts=PTS-STARTPTS,scale=3600:2160:flags=lanczos,fps=60,format=yuv420p[b36];
[b0][b1][b2][b3][b4][b5][b6][b7][b8][b9][b10][b11][b12][b13][b14][b15][b16][b17][b18][b19][b20][b21][b22][b23][b24][b25][b26][b27a][b27b][b28a][b28b][b28c1][b28h][b28c2][b31][b32][b34][b35][b35r][b36]concat=n=40:v=1:a=0,settb=AVTB[body];
[intro][body]xfade=transition=fade:duration=1:offset=30[vout]
'

cmd=(
  ffmpeg
  -y
  -i "$SRC_VIDEO"
  -i "$INTRO_CLIP"
  -i "$SD_CLIP"
  -i "$INDEXING_CLIP"
  -i "$RECAP_CLIP"
  -i "$SRC_AUDIO"
  -filter_complex "$FILTER"
  -map "[vout]"
  -map "5:a"
  -c:v libx264
  -preset slow
  -crf 18
  -pix_fmt yuv420p
  -c:a copy
  -movflags +faststart
  -shortest
  "$OUT"
)

printf 'FFmpeg command before render:\n'
printf '%q ' "${cmd[@]}"
printf '\n'

"${cmd[@]}"
