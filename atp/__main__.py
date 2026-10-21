"""反躺平机器人 — the laptop side.

    python -m atp                  run: phone triggers on :8765, keys below, watches the keyboard/mouse
    python -m atp --fake           same, with a robot that only prints (no ROS)
    python -m atp route desk       walk one route (desk, bed, pull) to tune it; add --back for the way back
    python -m atp motion wave      play one motion (wave, dance0, dance1)
    python -m atp setup            press Y once: the robot listens to /cmd_vel instead of the gamepad
    python -m atp idle             print keyboard/mouse idle seconds

Keys while running (then Enter): w work on/off · a alarm stopped · d desk · b bed · h home · q quit
"""

from __future__ import annotations

import socket
import sys
import threading

from .brain import Brain, Settings
from .idle import idle_seconds
from .robot import FakeRobot, RpoRobot, load_routes, reverse
from .server import serve
from .voice import Voice


def laptop_ip() -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        try:
            s.connect(("10.255.255.255", 1))
            return s.getsockname()[0]
        except OSError:
            return "127.0.0.1"


def run(robot) -> None:
    brain = Brain(robot, Voice(), load_routes(), Settings.from_env())
    serve(brain)
    print(f"phone: http://{laptop_ip()}:8765/alarm   keys: w a d b h q (then Enter)", flush=True)
    keys = {"w": lambda: brain.stop_work() if brain.work else brain.start_work(),
            "a": brain.alarm, "d": brain.desk, "b": brain.bed, "h": brain.home}

    quit = threading.Event()

    def read_keys():
        for line in sys.stdin:
            key = line.strip()[:1].lower()
            if key == "q":
                break
            keys.get(key, lambda: None)()
        quit.set()

    threading.Thread(target=read_keys, daemon=True).start()
    try:
        while not quit.wait(0.5):
            brain.tick(idle_seconds())
    except KeyboardInterrupt:
        pass


def main(argv: list[str]) -> None:
    fake = "--fake" in argv
    argv = [a for a in argv if a != "--fake"]
    robot = FakeRobot() if fake else RpoRobot()
    if not argv:
        run(robot)
    elif argv[0] == "route":
        steps = load_routes()[argv[1]]
        for step in reverse(steps) if "--back" in argv else steps:
            robot.walk(*step["walk"], step["secs"])
    elif argv[0] == "motion":
        robot.motion(argv[1], float(argv[2]) if len(argv) > 2 else Settings().motion_s)
    elif argv[0] == "setup":
        robot.take_cmd_vel()
    elif argv[0] == "idle":
        print(f"{idle_seconds():.1f}s")
    else:
        print(__doc__)


main(sys.argv[1:])
