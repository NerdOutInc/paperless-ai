#!/usr/bin/env python3
from __future__ import annotations

import math
import subprocess
import wave
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / "videos" / "paperless-ai-work"
SRC = WORK / "audio-source"
VOICE = WORK / "generated-voice"
OUT = WORK / "patched-audio"
OUT.mkdir(parents=True, exist_ok=True)


REPLACEMENTS = {
    "01-what-is-paperless-ngx": [
        (82.88, 83.91, "paperless-ai-v1.wav", "Paperless AI"),
    ],
    "02-what-we-added": [
        (41.24, 42.03, "paperless-ai-v1.wav", "Paperless AI"),
        (65.08, 66.22, "paperless-ai-v1.wav", "Paperless AI"),
        (94.97, 96.84, "paperless-ai-search-tool-v1.wav", "Paperless AI search tool"),
        (118.22, 119.64, "paperless-ai-v3.wav", "Paperless AI"),
        (129.30, 130.19, "paperless-ai-v1.wav", "Paperless AI"),
    ],
    "05-how-to-install-on-digital-ocean": [
        (7.52, 8.82, "paperless-ai-v3.wav", "Paperless AI"),
        (218.74, 220.28, "paperless-ai-add-on-v2.wav", "Paperless AI add-on"),
    ],
}


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def atempo_chain(factor: float) -> str:
    parts: list[float] = []
    remaining = factor
    while remaining > 2.0:
        parts.append(2.0)
        remaining /= 2.0
    while remaining < 0.5:
        parts.append(0.5)
        remaining /= 0.5
    parts.append(remaining)
    return ",".join(f"atempo={p:.8f}" for p in parts)


def wav_duration(path: Path) -> float:
    with wave.open(str(path), "rb") as wf:
        return wf.getnframes() / wf.getframerate()


def fit_clip(source: Path, duration: float, target: Path, sr: int) -> None:
    source_duration = wav_duration(source)
    factor = source_duration / duration
    filters = [
        f"aresample={sr}",
        "aformat=sample_fmts=s16:channel_layouts=mono",
        atempo_chain(factor),
        f"atrim=duration={duration:.6f}",
        "asetpts=PTS-STARTPTS",
    ]
    run([
        "ffmpeg",
        "-y",
        "-v",
        "error",
        "-i",
        str(source),
        "-af",
        ",".join(filters),
        str(target),
    ])


def read_wav(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as wf:
        sr = wf.getframerate()
        channels = wf.getnchannels()
        frames = wf.readframes(wf.getnframes())
    data = np.frombuffer(frames, dtype=np.int16)
    if channels > 1:
        data = data.reshape(-1, channels).mean(axis=1).astype(np.int16)
    return data.astype(np.float32) / 32768.0, sr


def write_wav(path: Path, data: np.ndarray, sr: int) -> None:
    clipped = np.clip(data, -1.0, 1.0)
    pcm = (clipped * 32767.0).astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes(pcm.tobytes())


def rms(data: np.ndarray) -> float:
    if len(data) == 0:
        return 0.0
    return float(math.sqrt(float(np.mean(np.square(data)))))


def apply_patch(audio: np.ndarray, sr: int, start: float, end: float, clip: np.ndarray) -> np.ndarray:
    start_i = max(0, int(round(start * sr)))
    end_i = min(len(audio), int(round(end * sr)))
    target_len = end_i - start_i
    if target_len <= 0:
        raise ValueError(f"Invalid patch interval: {start}-{end}")
    if len(clip) != target_len:
        x_old = np.linspace(0.0, 1.0, num=len(clip), endpoint=False)
        x_new = np.linspace(0.0, 1.0, num=target_len, endpoint=False)
        clip = np.interp(x_new, x_old, clip).astype(np.float32)

    original = audio[start_i:end_i]
    source_rms = rms(original)
    clip_rms = rms(clip)
    if source_rms > 0 and clip_rms > 0:
        clip = clip * min(2.2, max(0.35, source_rms / clip_rms))

    fade = min(int(0.035 * sr), target_len // 3)
    if fade > 0:
        ramp = np.linspace(0.0, 1.0, num=fade, endpoint=False, dtype=np.float32)
        clip[:fade] = original[:fade] * (1.0 - ramp) + clip[:fade] * ramp
        ramp_out = np.linspace(1.0, 0.0, num=fade, endpoint=False, dtype=np.float32)
        clip[-fade:] = clip[-fade:] * ramp_out + original[-fade:] * (1.0 - ramp_out)

    audio[start_i:end_i] = clip
    return audio


def main() -> None:
    for video_id, replacements in REPLACEMENTS.items():
        source_wav = SRC / f"{video_id}.wav"
        audio, sr = read_wav(source_wav)
        manifest: list[str] = []
        for idx, (start, end, clip_name, label) in enumerate(replacements, start=1):
            target_duration = end - start
            fitted = OUT / f"{video_id}-patch-{idx:02d}.wav"
            fit_clip(VOICE / clip_name, target_duration, fitted, sr)
            patch, patch_sr = read_wav(fitted)
            if patch_sr != sr:
                raise RuntimeError(f"Sample-rate mismatch: {patch_sr} != {sr}")
            audio = apply_patch(audio, sr, start, end, patch)
            manifest.append(f"{idx:02d}\t{start:.3f}\t{end:.3f}\t{label}\t{clip_name}\t{target_duration:.3f}s")
        out_wav = OUT / f"{video_id}-paperless-ai.wav"
        write_wav(out_wav, audio, sr)
        out_m4a = OUT / f"{video_id}-paperless-ai.m4a"
        run([
            "ffmpeg",
            "-y",
            "-v",
            "error",
            "-i",
            str(out_wav),
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            str(out_m4a),
        ])
        (OUT / f"{video_id}-patch-manifest.tsv").write_text("\n".join(manifest) + "\n")
        print(f"wrote {out_wav}")
        print(f"wrote {out_m4a}")


if __name__ == "__main__":
    main()
