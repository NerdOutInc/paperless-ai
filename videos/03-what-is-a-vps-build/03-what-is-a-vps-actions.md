# 03 - What Is A VPS Actions

## Source

- Audio: `/Users/brian/github/nerdoutinc/paperless-ai/videos/src/03-what-is-a-vps.m4a`
- Duration: 129.287 seconds
- Transcript: `/tmp/screen-studio-03-what-is-a-vps-transcript/transcript.json`
- Capture scope: full display with Screen Studio

## Visual Plan

Use two on-camera Helium tab scrolls:

1. Tab 1: `https://www.digitalocean.com/products/droplets`, scrolling the
   whole Droplets product page.
2. Tab 2: the DigitalOcean create-Droplet page, scrolling the whole form only.
   Do not click create, submit, resize, provision, or otherwise change account
   state.

Audio timing is a guide only. The recording just needs clean scrolling footage
for both pages.

## Transcript Cues

| Time | Narration cue | Planned screen |
| --- | --- | --- |
| 00:00-00:23 | Need somewhere to install Paperless; VPS definition | DigitalOcean Droplets product page |
| 00:23-00:58 | VPS as rented server space; DigitalOcean data centers | Continue Droplets product page scroll |
| 00:58-01:26 | DigitalOcean calls a VPS a Droplet; choose size and region | Create-Droplet page scroll |
| 01:26-02:09 | VPS is always on and online; later video creates one | Continue Create-Droplet page scroll |

## Setup Checks

- Helium first tab is the DigitalOcean Droplets product page.
- Helium second tab is the DigitalOcean create-Droplet page.
- The create-Droplet page is used for scrolling only; no Droplet creation is
  attempted.
- Codex and unrelated workbench apps are hidden before keeper recording.
- Old Screen Studio project windows are minimized before keeper recording.

## Rehearsal Sequence

1. Activate Helium and switch to tab 1 with `Command-1`.
2. Start at the top and scroll the entire Droplets product page to the bottom.
3. Switch to tab 2 with `Command-2`.
4. Start at the top and scroll the entire create-Droplet page to the bottom.
5. Reset both tabs to their top-of-page starting states.

## Coordinates And Helpers

- Safe Helium page focus point: `825,470`.
- Tab 1 command: `03-what-is-a-vps-helper.sh scroll-tab1`
- Tab 2 command: `03-what-is-a-vps-helper.sh scroll-tab2`
- Combined keeper command: `03-what-is-a-vps-helper.sh two-tab-scroll`

## Dry-Run Notes

- Dry run 1 reset both Helium tabs to the top, then scrolled tab 1 to the
  DigitalOcean footer and tab 2 to the create-Droplet bottom section. No
  account-changing control was clicked.
- After dry run 1, revised the helper so tab switching only moves the cursor
  over the page; it does not click inside the create-Droplet form.
- Dry run 2 repeated the combined two-tab sequence successfully from reset.
  Tab 1 reached the footer, and tab 2 reached the total-cost/Create Droplet
  area without submitting anything.
- Screen Studio keyboard start/stop smoke capture passed with a readable
  3.801667 second display track:
  `/Users/brian/Screen Studio Projects/Built-in Retina Display 2026-05-12 22:33:43.screenstudio`.
- Reused the existing status server on port 8765 with PIN `0618`. The keeper
  take had no actionable status notes.

## Keeper Result

- Screen Studio project:
  `/Users/brian/Screen Studio Projects/Built-in Retina Display 2026-05-12 22:37:03.screenstudio`
- Repo copy:
  `/Users/brian/github/nerdoutinc/paperless-ai/video-scripts/03-what-is-a-vps.screenstudio`
- Display track:
  `/Users/brian/github/nerdoutinc/paperless-ai/video-scripts/03-what-is-a-vps.screenstudio/recording/channel-1-display-0.mp4`
- Display-track duration: 187.555 seconds
- Contact sheet: `/tmp/03-vps-final-contact-sheet.jpg`
- Verdict: keeper. Frame review confirms the Droplets product page appears
  from the top through the footer, then the create-Droplet page appears through
  the bottom total-cost/Create Droplet area. No Droplet was created, and the
  sampled frames do not show Codex or Terminal.
