"""Seconds since the keyboard or mouse was last touched, from macOS (no camera)."""

import re
import subprocess


def idle_seconds() -> float:
    out = subprocess.run(["ioreg", "-c", "IOHIDSystem", "-d", "4"], capture_output=True, text=True).stdout
    match = re.search(r'"HIDIdleTime" = (\d+)', out)
    return int(match.group(1)) / 1e9 if match else 0.0
