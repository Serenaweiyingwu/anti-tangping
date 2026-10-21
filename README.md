# 反躺平机器人 (anti-tangping)

RoboParty RP0 盯着你干活：工作模式下你一停，它走到书桌边威胁你；闹钟停了你还不起，它走到床尾把被子拽走。
不用摄像头，只看键盘鼠标多久没动。这个仓库是笔记本这边，机器人那边只用 RP0 自带的走路和动作。

## How it works

- **Brain** (`atp/brain.py`) reads one number every 0.5 s: seconds since the keyboard or mouse was touched (`ioreg`).
  - Work mode on, idle ≥ `WORK_IDLE_S` → walk the `desk` route, threaten (worse every `THREAT_EVERY_S`); typing → walk back.
  - Alarm stopped → `WAKE_GRACE_S` to start typing. Typing → praise, work mode on. Otherwise → `bed` route, wake-up line,
    `pull` route (walks backwards with the blanket strapped to it), dance. Typing afterwards → home, work mode on.
- **Robot** (`atp/robot.py`): `robot_side/rpo_cmd.py` runs next to RP0's inference node over SSH and publishes
  `/cmd_vel` (walking) or `/joy` button presses (RB picks wave/dance0/dance1, LB plays it and LB again goes back to walking),
  exactly like the gamepad. Without `RPO_SSH` it drives turtlesim in `~/rp1-ros` instead.
- **Voice** (`atp/voice.py`): Doubao recordings in `voices/` (`tools/make_voices.py`), else macOS `say`, from the laptop speaker.
- **Phone** (`atp/server.py`): `http://<laptop-ip>:8765/alarm`, `/work/on`, `/work/off`, `/desk`, `/bed`, `/home`.

Defaults are demo-short (10 s idle, 20 s grace, 8 s between threats). Set `WORK_IDLE_S`, `WAKE_GRACE_S`, `THREAT_EVERY_S`,
`ACTIVE_S`, `MOTION_S` for real use. Routes are in `routes.json` (m/s, rad/s, seconds; RP0 clips vx to −0.4…0.6).

## On the robot day

RP0 must run the BeyondMimic config (`roboparty_inference robots/rpo/configs/beyondmimic.yaml`: walk + wave, dance0, dance1),
started and standing, with someone holding the e-stop and the gamepad (Y on the gamepad takes control back).

```bash
export RPO_SSH=user@robot-ip                 # RPO_ROS_SETUP if not /opt/ros/humble/setup.bash
python3 -m atp setup                         # press Y once; the inference log must say "Controlled by /cmd_vel"
python3 -m atp motion wave                   # 1. does a motion play and return to walking?
python3 -m atp route desk                    # 2. tune routes.json; --back walks it back
python3 -m atp route pull                    # 3. blanket test: light blanket, strap at the foot end, short pull
python3 -m atp                               # run; keys + Enter: w work · a alarm · d desk · b bed · h home · q quit
python3 -m atp --fake                        # same without a robot
```

Motion presses assume the selection starts at `wave` (fresh inference node). If RB was pressed on the gamepad, restart
the node or press RB until the log says `wave` is selected.

iPhone: Shortcuts → Automation → Alarm → "Is Stopped" → Run immediately → Get Contents of URL `http://<laptop-ip>:8765/alarm`
(same Wi-Fi; allow incoming connections for Python on the Mac).

## Tests

```bash
~/robo-translator/.venv/bin/python -m pytest -q tests     # any Python with pytest
```
