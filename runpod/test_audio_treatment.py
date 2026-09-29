#!/usr/bin/env python3
"""Prove the soundtrack is altered and the background voice is dropped."""
from __future__ import annotations

import json
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent / "stages"))
from audio_treatment import assess, render_voice, resolve_semitones  # noqa: E402


def fail(message: str) -> None:
    raise SystemExit(message)


def write_wav(path: Path, channels: list[np.ndarray], rate: int = 48000) -> None:
    stacked = np.stack(channels, axis=1)
    pcm = (np.clip(stacked, -1, 1) * 32767).astype(np.int16)
    with wave.open(str(path), "w") as handle:
        handle.setnchannels(pcm.shape[1])
        handle.setsampwidth(2)
        handle.setframerate(rate)
        handle.writeframes(pcm.tobytes())


def main() -> int:
    if abs(resolve_semitones({"pitch_shift": -1.0, "treatment": "cinematic"})) < 2:
        fail("a one-semitone profile still leaves the original voice in place")
    if resolve_semitones({"pitch_shift": 1.18, "treatment": "animated"}) == 1.18:
        fail("pitch_shift 1.18 is still being used as an unchanged playback ratio")

    rate = 48000
    seconds = 2
    samples = np.arange(rate * seconds) / rate
    voice = 0.4 * np.sin(2 * np.pi * 170 * samples) + 0.15 * np.sin(2 * np.pi * 340 * samples)
    voice *= 0.65 + 0.35 * np.sin(2 * np.pi * 3 * samples)
    room = 0.3 * np.sin(2 * np.pi * 860 * samples) + 0.12 * np.sin(2 * np.pi * 1040 * samples)
    with tempfile.TemporaryDirectory() as folder_name:
        folder = Path(folder_name)
        source = folder / "source.wav"
        output = folder / "altered.wav"
        write_wav(source, [voice + 0.15 * room, voice + 0.9 * room])
        report = render_voice(source, output, {"treatment": "cinematic", "pitch_shift": -1.0}, work=folder)
        if not report["passed"] or not report["voice_altered"] or not report["background_voice_suppressed"]:
            fail(f"treated voice was rejected: {report}")
        if not output.is_file():
            fail("treated voice file was removed")

        copied = folder / "copied.wav"
        write_wav(copied, [voice + 0.15 * room, voice + 0.9 * room])
        copied_report = assess(source, copied, folder / "background-voice.wav", semitones=-3)
        if copied_report["passed"] or "sound was not altered" not in copied_report["reasons"]:
            fail(f"an unchanged soundtrack was accepted: {copied_report}")
    print(json.dumps({"voice_gate": report}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
