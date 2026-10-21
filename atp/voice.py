"""The robot's voice, from the laptop speaker: a Doubao recording from voices/ if there is one
(tools/make_voices.py), otherwise macOS `say` with the Tingting voice. One line at a time."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

VOICES = Path(__file__).resolve().parent.parent / "voices"


def wav_path(text: str) -> Path:
    return VOICES / f"{hashlib.sha1(text.encode()).hexdigest()[:12]}.wav"


class Voice:
    def __init__(self):
        self.playing: subprocess.Popen | None = None

    def say(self, text: str) -> None:
        print(f"[voice] {text}", flush=True)
        if self.playing and self.playing.poll() is None:
            self.playing.terminate()
        wav = wav_path(text)
        cmd = ["afplay", str(wav)] if wav.exists() else ["say", "-v", "Tingting", text]
        self.playing = subprocess.Popen(cmd)


class QuietVoice:
    def say(self, text: str) -> None:
        print(f"[voice] {text}", flush=True)
