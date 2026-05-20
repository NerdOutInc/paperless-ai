# 04 - What Is Docker Actions

## Source

- Audio: `/Users/brian/github/nerdoutinc/paperless-ai/videos/src/04-what-is-docker.m4a`
- Duration: 120.419 seconds
- Transcript: `/tmp/screen-studio-04-what-is-docker-transcript/transcript.json`
- Capture scope: full display with Screen Studio

## Visual Plan

Use three on-camera anchors:

1. Helium on `https://www.docker.com/products/docker-desktop/`, scrolling from
   the hero section to the footer.
2. Docker Desktop on the Containers view with the cursor moved off the app so
   no hover states are active.
3. Terminal running `docker ps` when the narration says, "I'll show you them
   running in the terminal as well."

Audio timing is a guide only. The recording should clearly capture the intended states and leave post-production room to retime.

## Transcript Cues

| Time | Narration cue | Planned screen |
| --- | --- | --- |
| 00:00-00:10 | Intro: Docker used when setting up Paperless | Helium showing Docker website |
| 00:10-00:27 | Shipping-container metaphor; Docker does this for software | Scroll or hold Docker container/product explanation |
| 00:27-00:46 | Programs and dependencies packed into a container; same on desktop or VPS | Docker website, then prepare transition |
| 00:46-01:03 | "This is Docker Desktop on my Mac" and Paperless containers | Docker Desktop Containers view |
| 01:03-01:12 | "I'll show you them running in the terminal as well" | Terminal with `docker ps` |
| 01:12-01:34 | Containers keep things separate; Docker handles setup; restart containers safely | Terminal output, optionally scroll/hold on Paperless rows |
| 01:34-01:56 | Docker in a nutshell; setup script handles it | Hold readable Terminal output |
| 01:56-02:00 | Thanks | Clean final hold |

## Setup Checks

- Paperless stack responding at `http://localhost:8000`.
- Companion health responding at `http://localhost:3001/health`.
- `docker ps` shows Paperless containers, including `paperless-ai-app-1` and `paperless-ai-paperless-webserver-1`.
- Docker Desktop opens to a visible window, not tray-only.
- Helium opens to a Docker website page without address-bar focus.
- Terminal is ready in the repo with a clear prompt and the command `docker ps` available.
- Codex and unrelated workbench apps are hidden before keeper recording.
- Old Screen Studio project windows are minimized before keeper recording.

## Rehearsal Sequence

1. Open Helium to the selected Docker page.
2. Verify the page is loaded and visually useful without first-time banners blocking it.
3. Switch to Docker Desktop and confirm the Containers view shows the Paperless stack.
4. Switch to Terminal, run `docker ps`, and hold the output long enough to read.
5. Switch back to a clean final state for the outro.
6. Reset all three apps to their starting state.

## Coordinates And Helpers

To be filled during dry runs:

- Helium safe focus point:
- Docker website scroll command: `04-what-is-docker-helper.sh scroll-product-page`
- Docker Desktop Containers view coordinates:
- Terminal window focus point:
- Terminal command: `docker ps --filter name=paperless-ai --format "table {{.Names}}\t{{.Status}}"`
- Final hold state: Terminal output listing the Paperless containers and healthy status.

## Dry-Run Notes

- Discovery run: found and fixed duplicate Helium tabs, too-large website scroll, and unreadable wrapped `docker ps` output.
- Validation run: Helium opens cleanly to the Docker page, Docker Desktop shows the Paperless project, and formatted `docker ps` output is readable.
- Retake dry run 1: product page reaches the footer, Docker Desktop has no
  cursor hover state, and Terminal output is readable.
- Retake dry run 2: repeated the same product-page, Docker Desktop, and
  Terminal sequence successfully.
- Final keeper setup: fixed Terminal prep so `cd` and `clear` do not merge
  into one visible shell error before the Docker command.

## Keeper Result

- Screen Studio project:
  `/Users/brian/Screen Studio Projects/Built-in Retina Display 2026-05-12 20:15:36.screenstudio`
- Repo copy:
  `/Users/brian/github/nerdoutinc/paperless-ai/video-scripts/04-what-is-docker.screenstudio`
- Display track:
  `/Users/brian/Screen Studio Projects/Built-in Retina Display 2026-05-12 20:15:36.screenstudio/recording/channel-1-display-0.mp4`
- Display-track duration: 32.647 seconds
- Contact sheet: `/tmp/04-what-is-docker-final-contact-sheet.jpg`
- Frame review:
  - 00:00-00:16: Helium starts on Docker Desktop's product page and scrolls to
    the footer.
  - 00:18-00:22: Docker Desktop is visible on the `paperless-ai` project with
    the cursor off the app and no active hover state.
  - 00:24-00:32: Terminal is visible with formatted `docker ps` output listing
    `paperless-ai-app-1`, `paperless-ai-paperless-webserver-1`,
    `paperless-ai-redis-1`, and `paperless-ai-db-1` as healthy.
- Verdict: Keeper. The retake matches the user's requested three-shot sequence.
