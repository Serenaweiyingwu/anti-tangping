"""When the robot goes where, from one number: seconds since the keyboard or mouse was touched.

Work mode: idle too long -> walk to the desk and threaten, worse every round; typing again -> walk home.
Alarm: no typing within the grace time -> walk to the bed foot, walk back pulling the strapped blanket, celebrate;
typing (you got up and sat down) -> back home, work mode on. Typing first -> praise, work mode on.
"""

from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass

from . import lines
from .robot import reverse


@dataclass
class Settings:
    work_idle_s: float = 10  # idle this long in work mode -> robot comes
    active_s: float = 2  # touched within this -> you're working (or up)
    wake_grace_s: float = 20  # after the alarm stops, time to sit down at the desk
    threat_every_s: float = 8
    motion_s: float = 4

    @classmethod
    def from_env(cls) -> "Settings":
        names = {"work_idle_s": "WORK_IDLE_S", "active_s": "ACTIVE_S", "wake_grace_s": "WAKE_GRACE_S",
                 "threat_every_s": "THREAT_EVERY_S", "motion_s": "MOTION_S"}
        return cls(**{k: float(os.environ[v]) for k, v in names.items() if os.environ.get(v)})


class Brain:
    def __init__(self, robot, voice, routes: dict, settings: Settings, clock=time.monotonic, run_async=True):
        self.robot, self.voice, self.routes, self.s, self.clock = robot, voice, routes, settings, clock
        self.run_async = run_async
        self.lock = threading.RLock()
        self.busy = False
        self.work = False
        self.place = "home"
        self.alarm_at: float | None = None
        self.level = 0
        self.last_threat = 0.0

    # --- actions ---------------------------------------------------------------------------------------------

    def _perform(self, steps: list) -> None:
        def run():
            try:
                for kind, *args in steps:
                    if kind == "say":
                        self.voice.say(*args)
                    elif kind == "walk":
                        self.robot.walk(*args)
                    elif kind == "motion":
                        self.robot.motion(args[0], self.s.motion_s)
                    elif kind == "call":
                        args[0]()
            except Exception as e:  # noqa: BLE001 — a failed step must not kill the brain
                print(f"[brain] step failed: {e}", flush=True)
            finally:
                with self.lock:
                    self.busy = False

        self.busy = True
        if self.run_async:
            threading.Thread(target=run, daemon=True).start()
        else:
            run()

    def _route(self, steps: list) -> list:
        return [("walk", *step["walk"], step["secs"]) for step in steps]

    def _threat(self) -> list:
        line = lines.THREATS[min(self.level, len(lines.THREATS) - 1)]
        move = "wave" if self.level == 0 else ("dance1" if self.level % 2 else "dance0")
        self.level += 1
        return [("say", line), ("motion", move), ("call", self._threatened)]

    def _threatened(self) -> None:
        self.last_threat = self.clock()

    def _go_desk(self) -> None:
        self.place = "desk"
        self.level = 0
        self._perform([*self._route(self.routes["desk"]), *self._threat()])

    def _go_home(self, line: str) -> None:
        back = reverse(self.routes["desk"]) if self.place == "desk" else reverse(self.routes["bed"] + self.routes["pull"])
        self.place = "home"
        self.level = 0
        self._perform([("say", line), *self._route(back)])

    def _go_bed(self) -> None:
        self.alarm_at = None
        self.place = "bed"
        self._perform([
            *self._route(self.routes["bed"]),
            ("say", lines.WAKE_UP),
            *self._route(self.routes["pull"]),
            ("say", lines.TAKE_BLANKET),
            ("motion", "dance0"),
        ])

    # --- the loop --------------------------------------------------------------------------------------------

    def tick(self, idle_s: float) -> None:
        with self.lock:
            if self.busy:
                return
            now = self.clock()
            active = idle_s < self.s.active_s
            if self.alarm_at is not None:
                since = now - self.alarm_at
                if active and idle_s < since - 0.5:  # touched after the alarm stopped: up and at the desk
                    self.alarm_at = None
                    self.work = True
                    self._perform([("say", lines.GOT_UP_ALONE)])
                elif since >= self.s.wake_grace_s:
                    self._go_bed()
            elif self.place == "bed":
                if active:
                    self.work = True
                    self._go_home(lines.GOOD_MORNING)
            elif self.place == "desk":
                if active or not self.work:
                    self._go_home(lines.BACK_TO_WORK)
                elif now - self.last_threat >= self.s.threat_every_s:
                    self._perform(self._threat())
            elif self.work and idle_s >= self.s.work_idle_s:
                self._go_desk()

    # --- commands (phone, terminal keys) ---------------------------------------------------------------------

    def start_work(self) -> None:
        with self.lock:
            self.work = True
            self.voice.say(lines.WORK_ON)

    def stop_work(self) -> None:
        with self.lock:
            self.work = False
            self.voice.say(lines.WORK_OFF)

    def alarm(self) -> None:
        with self.lock:
            print("[brain] alarm stopped; waiting for you at the desk", flush=True)
            self.alarm_at = self.clock()

    def desk(self) -> None:
        with self.lock:
            if not self.busy and self.place == "home":
                self.work = True
                self._go_desk()

    def bed(self) -> None:
        with self.lock:
            if not self.busy and self.place == "home":
                self._go_bed()

    def home(self) -> None:
        with self.lock:
            if not self.busy and self.place != "home":
                self._go_home(lines.BACK_TO_WORK)
