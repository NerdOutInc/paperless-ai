#!/usr/bin/env python3
from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[2]
AUDIO = ROOT / "videos" / "paperless-ai-work" / "patched-audio"
OVERLAYS = ROOT / "videos" / "paperless-ai-work" / "visual-overlays"
OVERLAYS.mkdir(parents=True, exist_ok=True)
FONT = "/System/Library/Fonts/SFNS.ttf"
BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"


@dataclass(frozen=True)
class Patch:
    start: float
    end: float
    x: int
    y: int
    w: int
    h: int
    fontsize: int
    fg: str
    bg: str
    font: str = FONT
    pad_x: int = 4
    pad_y: int = 4
    mask_white: bool = False
    sample_time: float | None = None
    text: str = "AI"
    source_y: int | None = None
    feather: int = 0
    asset: str | None = None


PATCHES: dict[str, list[Patch]] = {
    "01-what-is-paperless-ngx": [
        Patch(4.0, 56.2, 1063, 227, 33, 26, 30, "0x111111", "0xffffff"),
        Patch(82.5, 90.2, 1063, 227, 33, 26, 30, "0x111111", "0xffffff"),
    ],
    "02-what-we-added": [
        Patch(
            0.0,
            4.0,
            0,
            0,
            3600,
            2160,
            0,
            "0xffffff",
            "0x000000",
            text="",
            asset="videos/paperless-ai-work/visual-overlays/title-cards/02-what-we-added-title-paperless-ai.png",
        ),
        Patch(4.0, 85.2, 1327, 79, 33, 26, 30, "0x111111", "0xffffff"),
        Patch(30.0, 82.0, 1063, 228, 33, 25, 30, "0x111111", "0xffffff"),
        Patch(52.0, 82.0, 1424, 391, 94, 69, 82, "0x111111", "0xffffff", BOLD, 8, 6),
        Patch(94.0, 121.0, 2013, 292, 48, 38, 44, "0x22201f", "0xefedeb", FONT, 6, 5),
        Patch(117.0, 131.5, 1668, 817, 51, 37, 43, "0x22201f", "0xefedeb", FONT, 6, 5),
    ],
    "05-how-to-install-on-digital-ocean": [
        Patch(
            0.0,
            4.0,
            0,
            0,
            3600,
            2160,
            0,
            "0xffffff",
            "0x000000",
            text="",
            asset="videos/paperless-ai-work/visual-overlays/title-cards/05-how-to-install-on-digital-ocean-title-paperless-ai.png",
        ),
        Patch(4.0, 28.2, 836, 82, 33, 26, 30, "0x111111", "0xffffff"),
        Patch(4.0, 265.7, 1053, 230, 33, 25, 30, "0x111111", "0xffffff"),
        Patch(4.0, 28.2, 1412, 392, 93, 68, 82, "0x111111", "0xffffff", BOLD, 8, 6),
    ],
}


def hex_to_rgba(value: str) -> tuple[int, int, int, int]:
    value = value.removeprefix("0x").removeprefix("#")
    return (int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16), 255)


def median_channel(pixels: list[tuple[int, int, int, int]], channel: int) -> int:
    values = sorted(pixel[channel] for pixel in pixels)
    return values[len(values) // 2]


def make_masked_overlay(source: Path, video_id: str, index: int, p: Patch, width: int, height: int) -> Image.Image:
    sample = OVERLAYS / f"{video_id}-source-patch-{index:02d}.png"
    crop_x = p.x - p.pad_x
    crop_y = p.y - p.pad_y
    sample_time = p.sample_time if p.sample_time is not None else p.start
    subprocess.run([
        "ffmpeg",
        "-y",
        "-v",
        "error",
        "-ss",
        f"{sample_time:.3f}",
        "-i",
        str(source),
        "-frames:v",
        "1",
        "-vf",
        f"crop={width}:{height}:{crop_x}:{crop_y}",
        str(sample),
    ], check=True)
    source_patch = Image.open(sample).convert("RGBA")
    width, height = source_patch.size
    pixels = list(source_patch.getdata())
    background_pixels = [pixel for pixel in pixels if not (pixel[0] > 150 and pixel[1] > 150 and pixel[2] > 150)]
    background = (
        median_channel(background_pixels, 0),
        median_channel(background_pixels, 1),
        median_channel(background_pixels, 2),
        255,
    )
    mask = Image.new("L", (width, height), 0)
    mask_out = mask.load()
    src = source_patch.load()
    for y in range(height):
        for x in range(width):
            r, g, b, _ = src[x, y]
            luminance = (0.2126 * r) + (0.7152 * g) + (0.0722 * b)
            if min(r, g, b) > 80 and luminance > 105:
                mask_out[x, y] = max(0, min(255, int((luminance - 80) * 2.2)))
    mask = mask.filter(ImageFilter.MaxFilter(11))
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    overlay.paste(Image.new("RGBA", (width, height), background), (0, 0), mask)
    return overlay


def make_sampled_overlay(source: Path, video_id: str, index: int, p: Patch, width: int, height: int) -> Image.Image:
    sample = OVERLAYS / f"{video_id}-title-bg-{index:02d}.png"
    sample_time = p.sample_time if p.sample_time is not None else p.start
    subprocess.run([
        "ffmpeg",
        "-y",
        "-v",
        "error",
        "-ss",
        f"{sample_time:.3f}",
        "-i",
        str(source),
        "-frames:v",
        "1",
        "-vf",
        f"crop={width}:{height}:{p.x}:{p.source_y}",
        str(sample),
    ], check=True)
    image = Image.open(sample).convert("RGBA")
    width, height = image.size
    if p.feather > 0:
        alpha = Image.new("L", (width, height), 255)
        alpha_out = alpha.load()
        for y in range(height):
            for x in range(width):
                distance = min(x, y, width - 1 - x, height - 1 - y)
                if distance < p.feather:
                    alpha_out[x, y] = int(255 * distance / p.feather)
        alpha = alpha.filter(ImageFilter.GaussianBlur(max(1, p.feather // 4)))
        image.putalpha(alpha)
    return image


def make_overlay(source: Path, video_id: str, index: int, p: Patch) -> Path:
    if p.asset is not None:
        return ROOT / p.asset
    width = p.w + p.pad_x * 2
    height = p.h + p.pad_y * 2
    if p.source_y is not None:
        image = make_sampled_overlay(source, video_id, index, p, width, height)
    elif p.mask_white:
        image = make_masked_overlay(source, video_id, index, p, width, height)
    else:
        image = Image.new("RGBA", (width, height), hex_to_rgba(p.bg))
    width, height = image.size
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(p.font, p.fontsize)
    bbox = draw.textbbox((0, 0), p.text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x = (width - tw) / 2 - bbox[0]
    y = (height - th) / 2 - bbox[1]
    draw.text((x, y), p.text, font=font, fill=hex_to_rgba(p.fg))
    path = OVERLAYS / f"{video_id}-overlay-{index:02d}.png"
    image.save(path)
    return path


def main() -> None:
    selected = set(sys.argv[1:])
    for video_id, patches in PATCHES.items():
        if selected and video_id not in selected:
            continue
        source = ROOT / "videos" / f"{video_id}.mp4"
        audio = AUDIO / f"{video_id}-paperless-ai.m4a"
        output = ROOT / "videos" / f"{video_id}-paperless-ai.mp4"
        overlay_paths = [make_overlay(source, video_id, idx, patch) for idx, patch in enumerate(patches, start=1)]
        cmd = ["ffmpeg", "-y", "-i", str(source), "-i", str(audio)]
        for overlay in overlay_paths:
            cmd.extend(["-loop", "1", "-i", str(overlay)])

        filters = ["[0:v]format=rgba[v0]"]
        last = "v0"
        for idx, patch in enumerate(patches, start=1):
            label = f"v{idx}"
            enable = f"between(t,{patch.start:.3f},{patch.end:.3f})"
            x = patch.x - patch.pad_x
            y = patch.y - patch.pad_y
            filters.append(f"[{last}][{idx + 1}:v]overlay={x}:{y}:enable='{enable}':eof_action=pass[{label}]")
            last = label
        filters.append(f"[{last}]format=yuv420p[vout]")
        cmd.extend([
            "-filter_complex",
            ";".join(filters),
            "-map",
            "[vout]",
            "-map",
            "1:a:0",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-r",
            "60",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            "-shortest",
            str(output),
        ])
        print("rendering", output)
        subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
