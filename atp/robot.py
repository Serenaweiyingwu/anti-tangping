"""The robot as the brain sees it: walk, play a motion, say a line, run a route.

RpoRobot runs robot_side/rpo_cmd.py next to RP0's inference node: over SSH on the robot (RPO_SSH=user@ip), or
locally in the ~/rp1-ros pixi env against turtlesim when RPO_SSH is unset. FakeRobot only prints.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HELPER = ROOT / "robot_side" / "rpo_cmd.py"

# RP0's BeyondMimic config (roboparty_inference robots/rpo/configs/beyondmimic.yaml): policy 0 walks, the rest
# play these motions. RB steps the selection (starts at wave), LB switches into it and LB again back to walking.
MOTIONS = ["wave", "dance0", "dance1"]
BUTTON_Y, BUTTON_LB, BUTTON_RB = 3, 4, 5


def load_routes(path: Path = ROOT / "routes.json") -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def reverse(route: list) -> list:
    """The way back: the same steps in reverse order, each walked the other way."""
    return [{"walk": [-v for v in step["walk"]], "secs": step["secs"]} for step in reversed(route)]


class FakeRobot:
    def __init__(self, speed: float = 1.0):
        self.speed = speed  # 0 in tests: no waiting

    def walk(self, vx: float, vy: float, wz: float, secs: float) -> None:
        print(f"[robot] walk vx={vx} vy={vy} wz={wz} for {secs}s", flush=True)
        time.sleep(secs * self.speed)

    def motion(self, name: str, secs: float) -> None:
        print(f"[robot] {name} for {secs}s", flush=True)
        time.sleep(secs * self.speed)

    def take_cmd_vel(self) -> None:
        print("[robot] press Y: /cmd_vel control", flush=True)


class RpoRobot(FakeRobot):
    def __init__(self):
        super().__init__()
        self.ssh = os.environ.get("RPO_SSH")
        self.ros_setup = os.environ.get("RPO_ROS_SETUP", "/opt/ros/humble/setup.bash")
        self.selected = 0  # RB selection; the inference node starts at the first motion
        self.copied = False

    def _run(self, *args: str) -> None:
        if not self.ssh:
            env = {**os.environ, "CMD_VEL_TOPIC": os.environ.get("CMD_VEL_TOPIC", "/turtle1/cmd_vel")}
            manifest = os.path.expanduser(os.environ.get("RPO_PIXI", "~/rp1-ros/pixi.toml"))
            cmd = ["pixi", "run", "--manifest-path", manifest, "python", str(HELPER), *args]
            subprocess.run(cmd, check=True, env=env)
            return
        if not self.copied:
            subprocess.run(["scp", "-q", str(HELPER), f"{self.ssh}:/tmp/rpo_cmd.py"], check=True)
            self.copied = True
        remote = f"source {shlex.quote(self.ros_setup)} && python3 /tmp/rpo_cmd.py {shlex.join(args)}"
        subprocess.run(["ssh", self.ssh, "bash", "-lc", shlex.quote(remote)], check=True)

    def walk(self, vx: float, vy: float, wz: float, secs: float) -> None:
        print(f"[robot] walk vx={vx} vy={vy} wz={wz} for {secs}s", flush=True)
        self._run("walk", str(vx), str(vy), str(wz), str(secs))

    def presses_for(self, name: str) -> list[int]:
        steps = (MOTIONS.index(name) - self.selected) % len(MOTIONS)
        return [BUTTON_RB] * steps + [BUTTON_LB]

    def motion(self, name: str, secs: float) -> None:
        print(f"[robot] {name} for {secs}s", flush=True)
        self._run("press", *map(str, self.presses_for(name)))
        self.selected = MOTIONS.index(name)
        time.sleep(secs)
        self._run("press", str(BUTTON_LB))

    def take_cmd_vel(self) -> None:
        """Y toggles gamepad / /cmd_vel. Check the inference log says 'Controlled by /cmd_vel' afterwards."""
        print("[robot] press Y: /cmd_vel control", flush=True)
        self._run("press", str(BUTTON_Y))
