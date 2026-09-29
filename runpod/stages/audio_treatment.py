#!/usr/bin/env python3
"""Replace the source soundtrack with a timed character voice.

The delivered proof kept the original recording. Pitch values in the saved
profiles are semitones, but the worker treated them as playback ratios and
then processed the whole mix, background voices included. This module does
the opposite: it keeps the foreground, throws away the room and side voices,
moves the locked profile by at least two semitones, and refuses a result that
still matches the source.
"""
from __future__ import annotations

import math
import subprocess
import wave
from pathlib import Path

import numpy as np


MIN_SEMITONES = 2.0
MAX_CORRELATION = 0.72
MAX_BACKGROUND_CORRELATION = 0.45
MAX_DRIFT_MS = 80.0
TREATMENT_SEMITONES = {
    "cinematic": -3.0,
    "warm": 2.0,
    "bright": 4.0,
    "deep": -5.0,
    "animated": 5.0,
    "natural": 3.0,
}
TREATMENT_EQ = {
    "cinematic": "equalizer=f=180:t=q:w=1:g=5,equalizer=f=2800:t=q:w=1:g=-4",
    "warm": "equalizer=f=160:t=q:w=1:g=6,equalizer=f=4500:t=q:w=1:g=-5",
    "bright": "equalizer=f=2500:t=q:w=1:g=5,equalizer=f=200:t=q:w=1:g=-2",
    "deep": "equalizer=f=120:t=q:w=1:g=6,equalizer=f=3500:t=q:w=1:g=-5",
    "animated": "equalizer=f=400:t=q:w=1:g=3,equalizer=f=3200:t=q:w=1:g=4",
    "natural": "equalizer=f=300:t=q:w=1:g=2,equalizer=f=2400:t=q:w=1:g=-2",
}


def resolve_semitones(profile: dict | None) -> float:
    profile = profile or {}
    treatment = str(profile.get("treatment") or profile.get("style") or "animated")
    fallback = TREATMENT_SEMITONES.get(treatment, 3.0)
    raw = profile.get("pitch_shift")
    if raw is None or raw == "":
        semis = fallback
    else:
        semis = float(raw)
        if abs(semis) > 12:
            raise ValueError("pitch_shift is semitones and must stay between -12 and 12")
    if abs(semis) < MIN_SEMITONES:
        direction = -1.0 if semis < 0 or (semis == 0 and fallback < 0) else 1.0
        semis = direction * max(abs(semis), abs(fallback), MIN_SEMITONES)
    return semis


def _run(command: list[str]) -> None:
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout or "ffmpeg failed")[-2000:])


def _duration(path: Path) -> float:
    completed = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path)],
        check=False, capture_output=True, text=True,
    )
    return float(completed.stdout.strip())


def _load_mono(path: Path) -> tuple[int, np.ndarray]:
    with wave.open(str(path)) as handle:
        channels = handle.getnchannels()
        rate = handle.getframerate()
        frames = np.frombuffer(handle.readframes(handle.getnframes()), dtype=np.int16).astype(np.float32)
    frames = frames.reshape(-1, channels).mean(axis=1) / 32767.0
    return rate, frames


def _correlation(left: np.ndarray, right: np.ndarray) -> float:
    count = min(left.size, right.size)
    if count == 0:
        return 1.0
    a = left[:count] - left[:count].mean()
    b = right[:count] - right[:count].mean()
    denom = float(np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 1.0
    return float(np.dot(a, b) / denom)


def _write_silence_bed(source: Path, bed: Path) -> None:
    """Side energy is the off-mic voice. Center dialogue cancels out."""
    _run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(source),
        "-filter_complex",
        "[0:a]aformat=sample_rates=48000:channel_layouts=stereo,pan=mono|c0=0.5*c0-0.5*c1,highpass=f=180,lowpass=f=3500[bed]",
        "-map", "[bed]", "-ac", "1", "-ar", "48000", str(bed),
    ])


def render_voice(source: Path, destination: Path, profile: dict | None = None, work: Path | None = None) -> dict:
    profile = profile or {}
    treatment = str(profile.get("treatment") or profile.get("style") or "animated")
    semitones = resolve_semitones(profile)
    ratio = 2 ** (semitones / 12.0)
    eq = TREATMENT_EQ.get(treatment, TREATMENT_EQ["animated"])
    duration = _duration(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    graph = (
        "[0:a]aformat=sample_rates=48000:channel_layouts=stereo,asplit=2[dry][bed];"
        "[dry]pan=mono|c0=0.5*c0+0.5*c1,highpass=f=110,lowpass=f=3600,"
        "afftdn=nr=14:nf=-30,agate=threshold=0.02:ratio=12:attack=8:release=160,"
        "speechnorm=e=12.5:r=0.0001:l=1,"
        f"rubberband=pitch={ratio:.6f},{eq},alimiter=limit=0.9[voice];"
        "[bed]pan=mono|c0=0.5*c0-0.5*c1,lowpass=f=140,afftdn=nr=30:nf=-50,volume=-26dB[room];"
        "[voice][room]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,"
        f"loudnorm=I=-16:TP=-1.5:LRA=11,apad=pad_dur={duration:.3f},atrim=0:{duration:.3f}[out]"
    )
    _run([
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(source),
        "-filter_complex", graph, "-map", "[out]", "-ac", "1", "-ar", "48000",
        str(destination),
    ])
    bed_path = (work or destination.parent) / "background-voice.wav"
    _write_silence_bed(source, bed_path)
    report = assess(source, destination, bed_path, semitones)
    report["treatment"] = treatment
    report["pitch_ratio"] = round(ratio, 5)
    if not report["passed"]:
        destination.unlink(missing_ok=True)
        raise RuntimeError("voice gate failed: " + "; ".join(report["reasons"]))
    return report


def assess(source: Path, output: Path, background: Path, semitones: float) -> dict:
    _, source_audio = _load_mono(source)
    _, output_audio = _load_mono(output)
    _, background_audio = _load_mono(background)
    source_correlation = abs(_correlation(source_audio, output_audio))
    background_correlation = abs(_correlation(background_audio, output_audio))
    drift_ms = abs(_duration(source) - _duration(output)) * 1000
    reasons: list[str] = []
    if abs(semitones) < MIN_SEMITONES:
        reasons.append("voice pitch was not moved")
    if source_correlation > MAX_CORRELATION:
        reasons.append("sound was not altered")
    if float(np.sqrt(np.mean(background_audio ** 2))) > 0.01 and background_correlation > MAX_BACKGROUND_CORRELATION:
        reasons.append("background voice is still in the mix")
    if drift_ms > MAX_DRIFT_MS:
        reasons.append(f"voice drifted {drift_ms:.0f} ms from the picture")
    return {
        "passed": not reasons,
        "reasons": reasons,
        "semitones": round(semitones, 2),
        "source_correlation": round(source_correlation, 3),
        "background_correlation": round(background_correlation, 3),
        "timing_drift_ms": round(drift_ms, 1),
        "voice_altered": "sound was not altered" not in reasons and "voice pitch was not moved" not in reasons,
        "background_voice_suppressed": "background voice is still in the mix" not in reasons,
    }
