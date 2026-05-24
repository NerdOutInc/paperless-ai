#!/usr/bin/env bash
set -euo pipefail

SRC_VIDEO="videos/src/06-install-raspberry-pi.mp4"
SRC_AUDIO="videos/src/06-install-raspberry-pi.m4a"
INTRO_CLIP="videos/06-install-raspberry-pi-build/hyperframes-rpi-slides/clips/rpi-intro-hyperframes-rev4.mp4"
SD_CLIP="videos/06-install-raspberry-pi-build/hyperframes-rpi-slides/clips/rpi-sd-insert-hyperframes-rev4.mp4"
OUT="videos/06-install-raspberry-pi-build/renders/06-install-raspberry-pi-rev4-preview.mp4"

FILTER='
[1:v]trim=start=0:end=31,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,settb=AVTB[intro];
[0:v]trim=start=4:end=4.5,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=9.42[b0];
[0:v]trim=start=4.5:end=20.5,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=17.38[b1];
[0:v]trim=start=20.5:end=24,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=5.0[b2];
[0:v]trim=start=24:end=28.2,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p[b3];
[0:v]trim=start=28.2:end=30.0,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=1.2[b4];
[0:v]trim=start=30.2:end=33.2,setpts=(PTS-STARTPTS)*0.6666666667,scale=1280:768:flags=lanczos,fps=60,format=yuv420p[b5];
[0:v]trim=start=33.2:end=36.2,setpts=(PTS-STARTPTS)*0.4166666667,scale=1280:768:flags=lanczos,fps=60,format=yuv420p[b6];
[0:v]trim=start=36.2:end=41.2,setpts=(PTS-STARTPTS)*0.58,scale=1280:768:flags=lanczos,fps=60,format=yuv420p[b7];
[0:v]trim=start=41.2:end=43.2,setpts=(PTS-STARTPTS)*0.625,scale=1280:768:flags=lanczos,fps=60,format=yuv420p[b8];
[0:v]trim=start=43.2:end=47.5,setpts=(PTS-STARTPTS)*0.6046511628,scale=1280:768:flags=lanczos,fps=60,format=yuv420p[b9];
[0:v]trim=start=47.5:end=47.516667,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=9.483333[b10];
[0:v]trim=start=48:end=59,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=9.34[b11];
[0:v]trim=start=59:end=62,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=4.16[b12];
[0:v]trim=start=62:end=74,setpts=(PTS-STARTPTS)*1.5833333333,scale=1280:768:flags=lanczos,fps=60,format=yuv420p[b13];
[2:v]trim=start=0:end=10,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,fade=t=in:st=0:d=0.75:color=white,fade=t=out:st=9.25:d=0.75:color=black[b14];
[0:v]trim=start=79:end=81,setpts=(PTS-STARTPTS)*2.0,scale=1280:768:flags=lanczos,fps=60,format=yuv420p[b15];
[0:v]trim=start=81:end=81.016667,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=13.983333[b16];
[0:v]trim=start=81:end=82,setpts=(PTS-STARTPTS)*3.0,scale=1280:768:flags=lanczos,fps=60,format=yuv420p[b17];
[0:v]trim=start=82:end=82.016667,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=4.983333[b18];
[0:v]trim=start=82:end=85,setpts=(PTS-STARTPTS)*0.3333333333,scale=1280:768:flags=lanczos,fps=60,format=yuv420p[b19];
[0:v]trim=start=85:end=85.016667,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=9.983333[b20];
[0:v]trim=start=85:end=116,setpts=(PTS-STARTPTS)*0.6129032258,scale=1280:768:flags=lanczos,fps=60,format=yuv420p[b21];
[0:v]trim=start=116:end=116.016667,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=5.563333[b22];
[0:v]trim=start=116:end=121.5,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=15.58[b23];
[0:v]trim=start=121.5:end=132,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=16.66[b24];
[0:v]trim=start=132:end=132.5,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=6.96[b25];
[0:v]trim=start=132.5:end=138.5,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=18.0[b26];
[0:v]trim=start=138.5:end=142.5,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=0.22[b27];
[0:v]trim=start=142.5:end=151,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p[b28];
[0:v]trim=start=151:end=156.5,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=15.14[b29];
[0:v]trim=start=156.5:end=166.5,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=25.88[b30];
[0:v]trim=start=166.5:end=181.5,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p,tpad=stop_mode=clone:stop_duration=15.480975[b31];
[0:v]trim=start=181.5:end=184.216667,setpts=PTS-STARTPTS,scale=1280:768:flags=lanczos,fps=60,format=yuv420p[b32];
[b0][b1][b2][b3][b4][b5][b6][b7][b8][b9][b10][b11][b12][b13][b14][b15][b16][b17][b18][b19][b20][b21][b22][b23][b24][b25][b26][b27][b28][b29][b30][b31][b32]concat=n=33:v=1:a=0,settb=AVTB[body];
[intro][body]xfade=transition=fade:duration=1:offset=30[vout]
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
