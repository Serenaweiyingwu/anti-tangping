"""The brain against a fake clock, a recording robot and an idle time we set by hand."""

import pytest

from atp import lines
from atp.brain import Brain, Settings
from atp.robot import BUTTON_LB, BUTTON_RB, RpoRobot, load_routes, reverse

ROUTES = {
    "desk": [{"walk": [0.3, 0, 0], "secs": 4}],
    "bed": [{"walk": [0.3, 0, 0], "secs": 3}, {"walk": [0, 0, 0.5], "secs": 2}],
    "pull": [{"walk": [-0.3, 0, 0], "secs": 3}],
}


class Log:
    def __init__(self):
        self.events = []

    def walk(self, vx, vy, wz, secs):
        self.events.append(("walk", vx, vy, wz, secs))

    def motion(self, name, secs):
        self.events.append(("motion", name))

    def say(self, text):
        self.events.append(("say", text))

    def take(self):
        events, self.events = self.events, []
        return events


@pytest.fixture
def world():
    log = Log()
    clock = [100.0]
    brain = Brain(log, log, ROUTES, Settings(), clock=lambda: clock[0], run_async=False)
    return brain, log, clock


def test_stopping_in_work_mode_brings_it_to_the_desk_and_typing_sends_it_home(world):
    brain, log, clock = world
    brain.start_work()
    log.take()
    brain.tick(idle_s=5)
    assert log.take() == []
    brain.tick(idle_s=11)
    assert log.take() == [("walk", 0.3, 0, 0, 4), ("say", lines.THREATS[0]), ("motion", "wave")]
    brain.tick(idle_s=1)
    assert log.take() == [("say", lines.BACK_TO_WORK), ("walk", -0.3, 0, 0, 4)]
    assert brain.place == "home"


def test_it_gets_worse_until_you_work(world):
    brain, log, clock = world
    brain.start_work()
    brain.tick(idle_s=11)
    log.take()
    brain.tick(idle_s=13)
    assert log.take() == []  # not yet: one threat every 8 s
    clock[0] += 8
    brain.tick(idle_s=21)
    assert log.take() == [("say", lines.THREATS[1]), ("motion", "dance1")]
    clock[0] += 8
    brain.tick(idle_s=29)
    assert log.take() == [("say", lines.THREATS[2]), ("motion", "dance0")]


def test_nobody_gets_up_after_the_alarm_so_the_blanket_goes(world):
    brain, log, clock = world
    brain.alarm()
    clock[0] += 10
    brain.tick(idle_s=600)
    assert log.take() == []
    clock[0] += 10
    brain.tick(idle_s=600)
    assert log.take() == [
        ("walk", 0.3, 0, 0, 3), ("walk", 0, 0, 0.5, 2), ("say", lines.WAKE_UP),
        ("walk", -0.3, 0, 0, 3), ("say", lines.TAKE_BLANKET), ("motion", "dance0"),
    ]
    brain.tick(idle_s=1)  # up and typing: home the way it came, work mode on
    assert log.take() == [("say", lines.GOOD_MORNING), ("walk", 0.3, 0, 0, 3), ("walk", 0, 0, -0.5, 2),
                          ("walk", -0.3, 0, 0, 3)]
    assert brain.work and brain.place == "home"


def test_typing_before_the_grace_time_is_up_keeps_the_blanket(world):
    brain, log, clock = world
    brain.alarm()
    clock[0] += 5
    brain.tick(idle_s=6)  # last touched before the alarm: still in bed
    clock[0] += 5
    brain.tick(idle_s=1)
    assert log.take() == [("say", lines.GOT_UP_ALONE)]
    assert brain.work and brain.alarm_at is None
    clock[0] += 30
    brain.tick(idle_s=1)
    assert log.take() == []


def test_motion_presses_step_the_selection_then_switch_in():
    robot = RpoRobot()
    assert robot.presses_for("wave") == [BUTTON_LB]
    assert robot.presses_for("dance1") == [BUTTON_RB, BUTTON_RB, BUTTON_LB]
    robot.selected = 2
    assert robot.presses_for("wave") == [BUTTON_RB, BUTTON_LB]


def test_routes_file_and_the_way_back():
    routes = load_routes()
    assert {"desk", "bed", "pull"} <= routes.keys()
    assert reverse(ROUTES["bed"]) == [{"walk": [0, 0, -0.5], "secs": 2}, {"walk": [-0.3, 0, 0], "secs": 3}]
