"""Record every line in atp/lines.py with Doubao TTS into voices/, using robo-translator's client and keys.

    ~/robo-translator/.venv/bin/python tools/make_voices.py

Lines already recorded are skipped. Without recordings the robot speaks with macOS `say`.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TRANSLATOR = Path(os.environ.get("ROBO_TRANSLATOR", "~/robo-translator")).expanduser()
sys.path[:0] = [str(ROOT), str(TRANSLATOR)]

from atp import lines  # noqa: E402
from atp.voice import wav_path  # noqa: E402

os.chdir(TRANSLATOR)  # robo.config reads .env from the working directory
from robo.audio import to_wav  # noqa: E402
from robo.config import load_settings  # noqa: E402
from robo.doubao import TTS_SAMPLE_RATE, Doubao  # noqa: E402

doubao = Doubao(load_settings())
for text in lines.ALL:
    path = wav_path(text)
    if path.exists():
        continue
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(to_wav(doubao.speak(text, "zh"), TTS_SAMPLE_RATE))
    print(f"{path.name}  {text}")
