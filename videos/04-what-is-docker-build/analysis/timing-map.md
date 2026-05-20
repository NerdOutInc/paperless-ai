# Timing Map

This is an evidence scaffold for review. It is not a render spec.

## Summary

- Source video: `videos/src/04-what-is-docker.mp4`
- Narration audio: `videos/src/04-what-is-docker.m4a`
- Video duration: 31.000s
- Narration duration: 120.419s
- Duration delta: 89.419s

## Artifacts

- media_summary: `videos/04-what-is-docker-build/analysis/media-summary.json`
- transcript: `videos/04-what-is-docker-build/analysis/transcript.json`
- screen_events: `videos/04-what-is-docker-build/analysis/screen-events.json`
- screen_events_contact_sheet: `videos/04-what-is-docker-build/analysis/screen-events-contact-sheet.jpg`
- timing_map_markdown: `videos/04-what-is-docker-build/analysis/timing-map.md`
- timing_map_json: `videos/04-what-is-docker-build/analysis/timing-map.json`

## Warnings

- Narration is 89.4s longer than the source video.

## Review Checklist

- Confirm high-confidence narration/screen matches visually.
- Review low-confidence rows before building an edit spec.
- Treat stable holds as candidates for trims, speed changes, or freeze frames.
- Use OCR text as supporting evidence, not proof of final alignment.

## Timing Rows

| Narration | Narration Time | Likely Source Range | Nearby Evidence | Proposed Operation | Confidence | Notes / Questions |
| --- | --- | --- | --- | --- | --- | --- |
| Hey, this is Brian from Fullstack Egg. | 0.000s - 3.080s | 0.000s - 7.000s | ocr_change e002 @ 3.000s: Docker Desktop.' The #': https'.Ilwww.docker.comlproduct5ldocker-desktopl Produ...; ocr_change e004 @ 5.000s: Docker Desktop.' The #... | align_to_event | medium | Narration is 89.4s longer than the source video overall. |
| When we set up paperless, | 3.080s - 4.920s | 0.000s - 7.000s | ocr_change e002 @ 3.000s: Docker Desktop.' The #': https'.Ilwww.docker.comlproduct5ldocker-desktopl Produ...; ocr_change e004 @ 5.000s: Docker Desktop.' The #... | align_to_event | medium | Narration is 89.4s longer than the source video overall. |
| we use something called Docker, | 4.920s - 7.560s | 0.000s - 7.000s | ocr_change e002 @ 3.000s: Docker Desktop.' The #': https'.Ilwww.docker.comlproduct5ldocker-desktopl Produ...; ocr_change e004 @ 5.000s: Docker Desktop.' The #... | align_to_event | high | OCR text overlaps the narration cue.; Narration is 89.4s longer than the source video overall. |
| and I'm going to tell you a little bit about it. | 7.560s - 10.360s | 0.000s - 7.000s | ocr_change e002 @ 3.000s: Docker Desktop.' The #': https'.Ilwww.docker.comlproduct5ldocker-desktopl Produ...; ocr_change e004 @ 5.000s: Docker Desktop.' The #... | align_to_event | medium | Narration is 89.4s longer than the source video overall. |
| You can think of Docker like a collection of shipping containers that all have different things inside, | 10.360s - 16.520s | 0.000s - 7.000s | ocr_change e002 @ 3.000s: Docker Desktop.' The #': https'.Ilwww.docker.comlproduct5ldocker-desktopl Produ...; ocr_change e004 @ 5.000s: Docker Desktop.' The #... | align_to_event | medium | Narration is 89.4s longer than the source video overall. |
| but because they are all inside of that same container, | 16.520s - 21.040s | 1.000s - 19.000s | ocr_change e004 @ 5.000s: Docker Desktop.' The # https'.Ilwww.docker.comlproductsldocker-desktopl Product...; ocr_change e002 @ 3.000s: Docker Desktop.' The #'... | align_to_event | medium | Narration is 89.4s longer than the source video overall. |
| it makes it really easy to manage, | 21.040s - 23.640s | 1.000s - 19.000s | ocr_change e004 @ 5.000s: Docker Desktop.' The # https'.Ilwww.docker.comlproductsldocker-desktopl Product...; ocr_change e002 @ 3.000s: Docker Desktop.' The #'... | align_to_event | medium | Narration is 89.4s longer than the source video overall. |
| and Docker does the same thing for software. | 23.640s - 27.080s | 1.000s - 19.000s | ocr_change e004 @ 5.000s: Docker Desktop.' The # https'.Ilwww.docker.comlproductsldocker-desktopl Product...; ocr_change e005 @ 10.000s: Docker Desktop.' The #... | align_to_event | medium | Narration is 89.4s longer than the source video overall. |
| Instead of installing a program and hoping it works on your computer, | 27.080s - 31.480s | 1.000s - 19.000s | ocr_change e005 @ 10.000s: Docker Desktop.' The #-, https'.Ilwww.docker.comlproductsldocker-desktopl Produ...; ocr_change e004 @ 5.000s: Docker Desktop.' The #... | align_to_event | medium | Narration is 89.4s longer than the source video overall. |
| everything the program needs gets packed into a container. | 31.480s - 35.240s | 1.000s - 19.000s | ocr_change e005 @ 10.000s: Docker Desktop.' The #-, https'.Ilwww.docker.comlproductsldocker-desktopl Produ...; ocr_change e004 @ 5.000s: Docker Desktop.' The #... | align_to_event | medium | Narration is 89.4s longer than the source video overall. |
| So when you run that container, it just works, | 35.240s - 38.640s | 1.000s - 19.000s | ocr_change e005 @ 10.000s: Docker Desktop.' The #-, https'.Ilwww.docker.comlproductsldocker-desktopl Produ...; ocr_change e004 @ 5.000s: Docker Desktop.' The #... | align_to_event | medium | Narration is 89.4s longer than the source video overall. |
| and it doesn't matter if you're running it on your desktop computer | 38.640s - 42.520s | 1.000s - 19.000s | ocr_change e005 @ 10.000s: Docker Desktop.' The #-, https'.Ilwww.docker.comlproductsldocker-desktopl Produ...; ocr_change e008 @ 15.000s: Docker Desktop.' The... | align_to_event | medium | Narration is 89.4s longer than the source video overall. |
| or on a VPS in the cloud, it always works the same. | 42.520s - 46.800s | 1.000s - 19.000s | ocr_change e005 @ 10.000s: Docker Desktop.' The #-, https'.Ilwww.docker.comlproductsldocker-desktopl Produ...; ocr_change e008 @ 15.000s: Docker Desktop.' The... | align_to_event | medium | Narration is 89.4s longer than the source video overall. |
| So this is Docker desktop on my Mac, | 46.800s - 50.640s | 8.000s - 20.000s | ocr_change e008 @ 15.000s: Docker Desktop.' The #'. https'.Ilwww.docker.comlproductsldocker-desktopl Produ...; ocr_change e005 @ 10.000s: Docker Desktop.' The... | align_to_event | high | OCR text overlaps the narration cue.; Narration is 89.4s longer than the source video overall. |
| and these are the containers running paperless right now on my computer. | 50.640s - 55.000s | 8.000s - 20.000s | ocr_change e010 @ 18.000s: *dockerdesktop PERSONAL Q Search Sign in Gordon paperless-ai IUsers/brianlgithu...; ocr_change e008 @ 15.000s: Docker Desktop.' The... | align_to_event | medium | Narration is 89.4s longer than the source video overall. |
| There's a few of them working together, one for the database, | 55.000s - 58.440s | 8.000s - 20.000s | ocr_change e008 @ 15.000s: Docker Desktop.' The #'. https'.Ilwww.docker.comlproductsldocker-desktopl Produ...; ocr_change e009 @ 17.000s: Docker Desktop.' The... | align_to_event | medium | Narration is 89.4s longer than the source video overall. |
| one for paperless itself, | 58.440s - 60.320s | 8.000s - 20.000s | ocr_change e010 @ 18.000s: *dockerdesktop PERSONAL Q Search Sign in Gordon paperless-ai IUsers/brianlgithu...; ocr_change e008 @ 15.000s: Docker Desktop.' The... | align_to_event | high | OCR text overlaps the narration cue.; Narration is 89.4s longer than the source video overall. |
| and one for the search add-on that we built. | 60.320s - 63.480s | 13.000s - 23.000s | ocr_change e010 @ 18.000s: *dockerdesktop PERSONAL Q Search Sign in Gordon paperless-ai IUsers/brianlgithu...; ocr_change e008 @ 15.000s: Docker Desktop.' The... | align_to_event | high | OCR text overlaps the narration cue.; Narration is 89.4s longer than the source video overall. |
| And here I'll show you them running in the terminal as well. | 63.480s - 67.600s | 13.000s - 23.000s | ocr_change e009 @ 17.000s: Docker Desktop.' The #". https'.Ilwww.docker.comlproductsldocker-desktopl Produ...; ocr_change e010 @ 18.000s: *dockerdesktop PERSON... | align_to_event | medium | Narration is 89.4s longer than the source video overall. |
| Each one is running in its own little box, | 67.600s - 70.000s | 13.000s - 23.000s | ocr_change e010 @ 18.000s: *dockerdesktop PERSONAL Q Search Sign in Gordon paperless-ai IUsers/brianlgithu...; ocr_change e009 @ 17.000s: Docker Desktop.' The... | align_to_event | medium | Narration is 89.4s longer than the source video overall. |
| keeping things clean and separate. | 70.000s - 72.320s | 13.000s - 23.000s | ocr_change e010 @ 18.000s: *dockerdesktop PERSONAL Q Search Sign in Gordon paperless-ai IUsers/brianlgithu...; ocr_change e009 @ 17.000s: Docker Desktop.' The... | align_to_event | medium | Narration is 89.4s longer than the source video overall. |
| And while this all might seem complicated, | 72.320s - 75.040s | 13.000s - 23.000s | ocr_change e010 @ 18.000s: *dockerdesktop PERSONAL Q Search Sign in Gordon paperless-ai IUsers/brianlgithu...; ocr_change e009 @ 17.000s: Docker Desktop.' The... | align_to_event | medium | Narration is 89.4s longer than the source video overall. |
| you really don't have to be a programmer to set this up. | 75.040s - 78.080s | 13.000s - 23.000s | ocr_change e013 @ 21.000s: • • • Ai paperless-ai--bash- 126x42 erless-ag on P vps-and-docker-videos 1$171; ocr_change e010 @ 18.000s: *dockerdesktop PERSONAL Q... | align_to_event | medium | Narration is 89.4s longer than the source video overall. |
| Docker handles all the complicated parts. | 78.080s - 81.000s | 15.000s - 27.000s | ocr_change e013 @ 21.000s: • • • Ai paperless-ai--bash- 126x42 erless-ag on P vps-and-docker-videos 1$171; ocr_change e009 @ 17.000s: Docker Desktop.' The #".... | align_to_event | medium | Narration is 89.4s longer than the source video overall. |
| You basically say, "Run this," | 81.000s - 83.080s | 15.000s - 27.000s | ocr_change e013 @ 21.000s: • • • Ai paperless-ai--bash- 126x42 erless-ag on P vps-and-docker-videos 1$171; ocr_change e010 @ 18.000s: *dockerdesktop PERSONAL Q... | align_to_event | medium | Narration is 89.4s longer than the source video overall. |
| and it pulls everything down and starts it up. | 83.080s - 86.160s | 15.000s - 27.000s | ocr_change e013 @ 21.000s: • • • Ai paperless-ai--bash- 126x42 erless-ag on P vps-and-docker-videos 1$171; ocr_change e015 @ 25.000s: • • • Ai paperless-ai--ba... | align_to_event | medium | Narration is 89.4s longer than the source video overall. |
| And if something breaks, you throw away the container and start fresh. | 86.160s - 90.440s | 15.000s - 27.000s | ocr_change e013 @ 21.000s: • • • Ai paperless-ai--bash- 126x42 erless-ag on P vps-and-docker-videos 1$171; ocr_change e015 @ 25.000s: • • • Ai paperless-ai--ba... | align_to_event | medium | Narration is 89.4s longer than the source video overall. |
| Your data is stored separately, so nothing gets lost. | 90.440s - 94.400s | 16.000s - 27.000s | ocr_change e015 @ 25.000s: • • • Ai paperless-ai--bash- 126x42 paperloss-ag on tr vps-and-docker-videos 1$...; ocr_change e013 @ 21.000s: • • • Ai paperless-ai... | align_to_event | medium | Narration is 89.4s longer than the source video overall. |
| So that's Docker in a nutshell. | 94.400s - 96.760s | 19.000s - 31.000s | ocr_change e015 @ 25.000s: • • • Ai paperless-ai--bash- 126x42 paperloss-ag on tr vps-and-docker-videos 1$...; ocr_change e013 @ 21.000s: • • • Ai paperless-ai... | align_to_event | high | OCR text overlaps the narration cue.; Narration is 89.4s longer than the source video overall. |
| It packages software, so it runs the same everywhere, | 96.760s - 100.240s | 19.000s - 31.000s | ocr_change e015 @ 25.000s: • • • Ai paperless-ai--bash- 126x42 paperloss-ag on tr vps-and-docker-videos 1$...; ocr_change e013 @ 21.000s: • • • Ai paperless-ai... | align_to_event | medium | Narration is 89.4s longer than the source video overall. |
| and you don't have to worry about installing all these dependencies | 100.240s - 103.400s | 19.000s - 31.000s | ocr_change e015 @ 25.000s: • • • Ai paperless-ai--bash- 126x42 paperloss-ag on tr vps-and-docker-videos 1$...; ocr_change e013 @ 21.000s: • • • Ai paperless-ai... | align_to_event | medium | Narration is 89.4s longer than the source video overall. |
| and breaking things. | 103.400s - 105.400s | 19.000s - 31.000s | ocr_change e015 @ 25.000s: • • • Ai paperless-ai--bash- 126x42 paperloss-ag on tr vps-and-docker-videos 1$...; ocr_change e013 @ 21.000s: • • • Ai paperless-ai... | align_to_event | medium | Narration is 89.4s longer than the source video overall. |
| And for the paperless install videos, | 105.400s - 108.760s | 19.000s - 31.000s | ocr_change e015 @ 25.000s: • • • Ai paperless-ai--bash- 126x42 paperloss-ag on tr vps-and-docker-videos 1$...; stable_hold e016 @ 25.500s: • • • Ai paperless-a... | align_to_event | high | OCR text overlaps the narration cue.; Narration is 89.4s longer than the source video overall. |
| you'll see that our setup script handles all the Docker stuff for you, | 108.760s - 112.760s | 19.000s - 31.000s | ocr_change e015 @ 25.000s: • • • Ai paperless-ai--bash- 126x42 paperloss-ag on tr vps-and-docker-videos 1$...; stable_hold e016 @ 25.500s: • • • Ai paperless-a... | align_to_event | medium | Narration is 89.4s longer than the source video overall. |
| automatically, so you really don't have to worry about it. | 112.760s - 116.720s | 19.000s - 31.000s | ocr_change e015 @ 25.000s: • • • Ai paperless-ai--bash- 126x42 paperloss-ag on tr vps-and-docker-videos 1$...; stable_hold e016 @ 25.500s: • • • Ai paperless-a... | align_to_event | medium | Narration is 89.4s longer than the source video overall. |
| And that's it for now. | 116.720s - 118.160s | 19.000s - 31.000s | ocr_change e015 @ 25.000s: • • • Ai paperless-ai--bash- 126x42 paperloss-ag on tr vps-and-docker-videos 1$...; stable_hold e016 @ 25.500s: • • • Ai paperless-a... | align_to_event | medium | Narration is 89.4s longer than the source video overall. |
| Thanks again for watching. | 118.160s - 119.880s | 19.000s - 31.000s | ocr_change e015 @ 25.000s: • • • Ai paperless-ai--bash- 126x42 paperloss-ag on tr vps-and-docker-videos 1$...; stable_hold e016 @ 25.500s: • • • Ai paperless-a... | align_to_event | medium | Narration is 89.4s longer than the source video overall. |
