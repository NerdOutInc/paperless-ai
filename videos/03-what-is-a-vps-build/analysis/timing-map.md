# Timing Map

This is an evidence scaffold for review. It is not a render spec.

## Summary

- Source video: `/Users/brian/github/nerdoutinc/paperless-ai/videos/src/03-what-is-a-vps.mp4`
- Narration audio: `/Users/brian/github/nerdoutinc/paperless-ai/videos/src/03-what-is-a-vps.m4a`
- Video duration: 51.717s
- Narration duration: 129.335s
- Duration delta: 77.618s

## Artifacts

- media_summary: `/Users/brian/github/nerdoutinc/paperless-ai/videos/03-what-is-a-vps-build/analysis/media-summary.json`
- transcript: `/Users/brian/github/nerdoutinc/paperless-ai/videos/03-what-is-a-vps-build/analysis/transcript.json`
- screen_events: `/Users/brian/github/nerdoutinc/paperless-ai/videos/03-what-is-a-vps-build/analysis/screen-events.json`
- screen_events_contact_sheet: `/Users/brian/github/nerdoutinc/paperless-ai/videos/03-what-is-a-vps-build/analysis/screen-events-contact-sheet.jpg`
- timing_map_markdown: `/Users/brian/github/nerdoutinc/paperless-ai/videos/03-what-is-a-vps-build/analysis/timing-map.md`
- timing_map_json: `/Users/brian/github/nerdoutinc/paperless-ai/videos/03-what-is-a-vps-build/analysis/timing-map.json`

## Warnings

- Narration is 77.6s longer than the source video.

## Review Checklist

- Confirm high-confidence narration/screen matches visually.
- Review low-confidence rows before building an edit spec.
- Treat stable holds as candidates for trims, speed changes, or freeze frames.
- Use OCR text as supporting evidence, not proof of final alignment.

## Timing Rows

| Narration | Narration Time | Likely Source Range | Nearby Evidence | Proposed Operation | Confidence | Notes / Questions |
| --- | --- | --- | --- | --- | --- | --- |
| Hey, this is Brian from Fullstack Egg. | 0.000s - 3.700s | 0.000s - 7.000s | ocr_change e002 @ 5.000s: f DigitalOcean Droplets \| DigitalOcean 4 c https:Ilwww.digitslocean.comlproduct...; anchor e001 @ 5.000s: f DigitalOcean Droplets \| D... | align_to_event | medium | Narration is 77.6s longer than the source video overall. |
| Before we set up paperless, | 3.700s - 5.900s | 0.000s - 17.000s | ocr_change e002 @ 5.000s: f DigitalOcean Droplets \| DigitalOcean 4 c https:Ilwww.digitslocean.comlproduct...; stable_hold e003 @ 7.500s: r DigitalOcearh Drople... | align_to_event | medium | Narration is 77.6s longer than the source video overall. |
| we're going to need somewhere to install it. | 5.900s - 9.100s | 0.000s - 17.000s | ocr_change e002 @ 5.000s: f DigitalOcean Droplets \| DigitalOcean 4 c https:Ilwww.digitslocean.comlproduct...; stable_hold e003 @ 7.500s: r DigitalOcearh Drople... | align_to_event | medium | Narration is 77.6s longer than the source video overall. |
| We could install it on our own computer at home. | 9.100s - 13.980s | 0.000s - 17.000s | ocr_change e002 @ 5.000s: f DigitalOcean Droplets \| DigitalOcean 4 c https:Ilwww.digitslocean.comlproduct...; stable_hold e003 @ 7.500s: r DigitalOcearh Drople... | align_to_event | medium | Narration is 77.6s longer than the source video overall. |
| Or if we want to install it in the Cloud, | 13.980s - 16.540s | 0.000s - 17.000s | ocr_change e002 @ 5.000s: f DigitalOcean Droplets \| DigitalOcean 4 c https:Ilwww.digitslocean.comlproduct...; stable_hold e003 @ 7.500s: r DigitalOcearh Drople... | align_to_event | medium | Narration is 77.6s longer than the source video overall. |
| we could set up a VPS. | 16.540s - 19.220s | 0.000s - 17.000s | ocr_change e002 @ 5.000s: f DigitalOcean Droplets \| DigitalOcean 4 c https:Ilwww.digitslocean.comlproduct...; stable_hold e003 @ 7.500s: r DigitalOcearh Drople... | align_to_event | medium | Narration is 77.6s longer than the source video overall. |
| VPS stands for Virtual Private Server. | 19.220s - 23.140s | 0.000s - 17.000s | ocr_change e002 @ 5.000s: f DigitalOcean Droplets \| DigitalOcean 4 c https:Ilwww.digitslocean.comlproduct...; stable_hold e003 @ 7.500s: r DigitalOcearh Drople... | align_to_event | medium | Narration is 77.6s longer than the source video overall. |
| You can think of it as renting | 23.140s - 25.460s | 0.000s - 17.000s | ocr_change e002 @ 5.000s: f DigitalOcean Droplets \| DigitalOcean 4 c https:Ilwww.digitslocean.comlproduct...; stable_hold e003 @ 7.500s: r DigitalOcearh Drople... | align_to_event | medium | Narration is 77.6s longer than the source video overall. |
| a small office space instead of buying your own building. | 25.460s - 29.980s | 0.000s - 19.000s | scene_change e005 @ 17.000s: r DigitalOcean Droplets \| DigitalOcean 4 c https:Ilwww.digitslocean.comlproduct...; stable_hold e003 @ 7.500s: r DigitalOcearh Dro... | align_to_event | medium | Narration is 77.6s longer than the source video overall. |
| Someone else owns the building and handles all the maintenance, | 29.980s - 34.780s | 0.000s - 19.000s | scene_change e005 @ 17.000s: r DigitalOcean Droplets \| DigitalOcean 4 c https:Ilwww.digitslocean.comlproduct...; stable_hold e003 @ 7.500s: r DigitalOcearh Dro... | align_to_event | medium | Narration is 77.6s longer than the source video overall. |
| and you just use the space. | 34.780s - 37.940s | 8.000s - 22.000s | scene_change e005 @ 17.000s: r DigitalOcean Droplets \| DigitalOcean 4 c https:Ilwww.digitslocean.comlproduct...; anchor e004 @ 10.000s: f DigitalOcean Droplets... | align_to_event | medium | Narration is 77.6s longer than the source video overall. |
| Setting up a VPS is just like renting an office. | 37.940s - 42.620s | 14.107s - 28.000s | scene_change e005 @ 17.000s: r DigitalOcean Droplets \| DigitalOcean 4 c https:Ilwww.digitslocean.comlproduct...; stable_hold e007 @ 21.500s: f DigitalOcean Dro... | align_to_event | high | Narration is 77.6s longer than the source video overall. |
| A company like DigitalOcean has huge data centers full of servers. | 42.620s - 47.980s | 15.000s - 28.000s | scene_change e005 @ 17.000s: r DigitalOcean Droplets \| DigitalOcean 4 c https:Ilwww.digitslocean.comlproduct...; stable_hold e007 @ 21.500s: f DigitalOcean Dro... | align_to_event | high | Narration is 77.6s longer than the source video overall. |
| You rent just a slice of one of those servers. | 47.980s - 51.300s | 15.000s - 28.000s | scene_change e005 @ 17.000s: r DigitalOcean Droplets \| DigitalOcean 4 c https:Ilwww.digitslocean.comlproduct...; stable_hold e007 @ 21.500s: f DigitalOcean Dro... | align_to_event | medium | Narration is 77.6s longer than the source video overall. |
| It's always on, | 51.300s - 52.660s | 15.000s - 28.000s | scene_change e005 @ 17.000s: r DigitalOcean Droplets \| DigitalOcean 4 c https:Ilwww.digitslocean.comlproduct...; stable_hold e007 @ 21.500s: f DigitalOcean Dro... | align_to_event | medium | Narration is 77.6s longer than the source video overall. |
| always connected to the Internet, | 52.660s - 54.820s | 15.000s - 28.000s | scene_change e005 @ 17.000s: r DigitalOcean Droplets \| DigitalOcean 4 c https:Ilwww.digitslocean.comlproduct...; stable_hold e007 @ 21.500s: f DigitalOcean Dro... | align_to_event | medium | Narration is 77.6s longer than the source video overall. |
| and you can run whatever you want to install on it. | 54.820s - 58.340s | 20.624s - 30.500s | ocr_change e009 @ 27.500s: r DigitalOcearh Droplets \| DigitalOcean 4 C https:Ilwww.digitslocean.comlproduc...; ocr_change e010 @ 28.000s: t DigitalOcean Drople... | align_to_event | medium | Narration is 77.6s longer than the source video overall. |
| Here's what setting up a VPS actually looks like. | 58.340s - 62.260s | 22.112s - 32.000s | ocr_change e009 @ 27.500s: r DigitalOcearh Droplets \| DigitalOcean 4 C https:Ilwww.digitslocean.comlproduc...; ocr_change e010 @ 28.000s: t DigitalOcean Drople... | align_to_event | medium | Narration is 77.6s longer than the source video overall. |
| On DigitalOcean, they call a VPS a droplet. | 62.260s - 65.660s | 23.575s - 32.000s | ocr_change e009 @ 27.500s: r DigitalOcearh Droplets \| DigitalOcean 4 C https:Ilwww.digitslocean.comlproduc...; ocr_change e010 @ 28.000s: t DigitalOcean Drople... | align_to_event | medium | Narration is 77.6s longer than the source video overall. |
| You pick the size you need based on your software requirements. | 65.660s - 70.540s | 25.231s - 32.000s | ocr_change e009 @ 27.500s: r DigitalOcearh Droplets \| DigitalOcean 4 C https:Ilwww.digitslocean.comlproduc...; ocr_change e010 @ 28.000s: t DigitalOcean Drople... | align_to_event | medium | Narration is 77.6s longer than the source video overall. |
| For paperless, we're going to need something with about four gigs of memory. | 70.540s - 75.300s | 25.500s - 32.000s | ocr_change e012 @ 28.500s: t DigitalOce8rh Droplets \| DigitalOcean 4 c https:Ilwww.digitalocean.comlproduc...; ocr_change e014 @ 30.000s: f DigitalOcean Drople... | align_to_event | medium | Narration is 77.6s longer than the source video overall. |
| On DigitalOcean, that's going to run us about 24 bucks a month, | 75.300s - 79.740s | 25.500s - 32.998s | ocr_change e014 @ 30.000s: f DigitalOcean Droplets \| fj DigitalOcean 4 c https:Ilwww.digitslocean.comlprod...; ocr_change e012 @ 28.500s: t DigitalOce8rh Dropl... | align_to_event | medium | Narration is 77.6s longer than the source video overall. |
| which is less than a lot of software subscriptions, | 79.740s - 83.100s | 28.000s - 37.500s | ocr_change e015 @ 34.500s: f DigitalOcearh Droplets \| DigitalOcean 4 C https:Ilwww.digitalocean.comlproduc...; ocr_change e016 @ 35.000s: t DigitalOcean Drople... | align_to_event | medium | Narration is 77.6s longer than the source video overall. |
| and you own everything on it. | 83.100s - 85.860s | 28.000s - 37.500s | ocr_change e015 @ 34.500s: f DigitalOcearh Droplets \| DigitalOcean 4 C https:Ilwww.digitalocean.comlproduc...; ocr_change e016 @ 35.000s: t DigitalOcean Drople... | align_to_event | medium | Narration is 77.6s longer than the source video overall. |
| As you can see here, | 85.860s - 87.860s | 28.000s - 37.500s | ocr_change e015 @ 34.500s: f DigitalOcearh Droplets \| DigitalOcean 4 C https:Ilwww.digitalocean.comlproduc...; ocr_change e016 @ 35.000s: t DigitalOcean Drople... | align_to_event | medium | Narration is 77.6s longer than the source video overall. |
| you can choose the region your server lives in, | 87.860s - 90.660s | 32.500s - 42.000s | ocr_change e018 @ 35.500s: r DigitalOcean Droplets \| DigitalOcean 4 c https:Ilwww.digitslocean.comlproduct...; ocr_change e016 @ 35.000s: t DigitalOcean Drople... | align_to_event | medium | Narration is 77.6s longer than the source video overall. |
| so you're going to want to just choose whatever is closest to you. | 90.660s - 94.900s | 32.500s - 42.000s | ocr_change e018 @ 35.500s: r DigitalOcean Droplets \| DigitalOcean 4 c https:Ilwww.digitslocean.comlproduct...; ocr_change e016 @ 35.000s: t DigitalOcean Drople... | align_to_event | medium | Narration is 77.6s longer than the source video overall. |
| I'm sure when you hear $24 a month, | 94.900s - 97.980s | 33.500s - 43.500s | ocr_change e020 @ 40.000s: f DigitalOcean Droplets \| DigitalOcean https:Ilwww.digitslocean.comlproductsldr...; ocr_change e021 @ 41.000s: f DigitalOcean Drople... | align_to_event | medium | Narration is 77.6s longer than the source video overall. |
| you're thinking, "Why not just run this on my own computer?" | 97.980s - 101.900s | 33.500s - 43.500s | ocr_change e020 @ 40.000s: f DigitalOcean Droplets \| DigitalOcean https:Ilwww.digitslocean.comlproductsldr...; ocr_change e021 @ 41.000s: f DigitalOcean Drople... | align_to_event | medium | Narration is 77.6s longer than the source video overall. |
| You totally can do that, but a VPS is always on, | 101.900s - 105.860s | 38.000s - 47.000s | ocr_change e022 @ 41.500s: t DigitalOcean Droplets \| DigitalOcean 4 c https:Ilwww.digitalocean.comlproduct...; ocr_change e021 @ 41.000s: f DigitalOcean Drople... | align_to_event | medium | Narration is 77.6s longer than the source video overall. |
| even when your home Internet goes down or you turn off your laptop, | 105.860s - 110.340s | 39.000s - 47.500s | ocr_change e022 @ 41.500s: t DigitalOcean Droplets \| DigitalOcean 4 c https:Ilwww.digitalocean.comlproduct...; ocr_change e024 @ 45.000s: f DigitalOceark Dropl... | align_to_event | medium | Narration is 77.6s longer than the source video overall. |
| and when you want to access your documents from your phone in the field, | 110.340s - 113.940s | 42.841s - 50.000s | ocr_change e024 @ 45.000s: f DigitalOceark Droplets \| fj DigitalOcean * c https:Ilwww.digitalocean.comlpro...; ocr_change e025 @ 45.500s: ? DigitalOcean Drople... | align_to_event | medium | Narration is 77.6s longer than the source video overall. |
| the VPS is already on the Internet and ready to go. | 113.940s - 117.980s | 43.000s - 50.000s | ocr_change e027 @ 46.000s: DigitalOcean Droplets \| Sca', t DigitslOcean * c https:Ilcloud.digitalocean.com...; ocr_change e025 @ 45.500s: ? DigitalOcean Drople... | align_to_event | medium | Narration is 77.6s longer than the source video overall. |
| So that's it. A VPS is just a computer you write online. | 117.980s - 122.140s | 43.500s - 51.717s | ocr_change e028 @ 48.000s: ? DigitalOcean Droplets \| Sca, t DigitalOcean <- * C https:Ilcloud.digitalocean...; ocr_change e031 @ 50.000s: ? DigitalOcean Drople... | align_to_event | medium | Narration is 77.6s longer than the source video overall. |
| In a later video, we'll walk you through actually creating one of these | 122.140s - 125.740s | 44.000s - 51.717s | ocr_change e031 @ 50.000s: ? DigitalOcean Droplets \| Sca', t DigitslOcean <- * C https:Ilcloud.digitalocea...; ocr_change e032 @ 51.000s: ? DigitalOcean Drople... | align_to_event | medium | Narration is 77.6s longer than the source video overall. |
| and installing paperless on it step-by-step. | 125.740s - 128.940s | 44.000s - 51.717s | ocr_change e032 @ 51.000s: ? DigitalOcean Droplets \| Sca, \* DigitslOcean <- \* C https:Ilcloud.digitalocean...; ocr_change e031 @ 50.000s: ? DigitalOcean Drople... | align_to_event | medium | Narration is 77.6s longer than the source video overall. |
