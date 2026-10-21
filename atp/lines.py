"""What the robot says."""

# At the desk, getting worse each round until the owner types again.
THREATS = [
    "喂！你停下来了。",
    "继续工作！不许躺平！",
    "我数到三。一，二……",
    "再不动，我就一直站在这儿看着你。",
]
BACK_TO_WORK = "很好，继续保持。我先回去了。"

WAKE_UP = "起床了！太阳晒屁股了！"
TAKE_BLANKET = "被子没收！"
GOT_UP_ALONE = "不错，自己起来了。开始工作！"
GOOD_MORNING = "早上好！今天也要卷起来！"

WORK_ON = "工作模式开启。我盯着你呢。"
WORK_OFF = "工作模式关闭。辛苦了。"

ALL = [*THREATS, BACK_TO_WORK, WAKE_UP, TAKE_BLANKET, GOT_UP_ALONE, GOOD_MORNING, WORK_ON, WORK_OFF]
