"""Runs next to RP0's inference node (on the robot, or locally against turtlesim) and sends it one command.

    rpo_cmd.py walk VX VY WZ SECS     /cmd_vel at 20 Hz for SECS, then a stop
    rpo_cmd.py press BUTTON...        presses gamepad buttons on /joy, one at a time (LB=4, RB=5, Y=3)

The inference node acts on a button's rising edge, so each button is one press message and one release.
CMD_VEL_TOPIC / JOY_TOPIC override the topics (turtlesim: CMD_VEL_TOPIC=/turtle1/cmd_vel).
"""

import os
import sys
import time

import rclpy
from geometry_msgs.msg import Twist
from sensor_msgs.msg import Joy

RATE_HZ = 20
# Triggers (axes 2 and 5) rest at 1.0; the node turns on a trigger below 0.
JOY_AXES = [0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0, 0.0]
JOY_BUTTONS = 11


def wait_for_subscriber(node, pub, timeout_s=3.0):
    end = time.monotonic() + timeout_s
    while pub.get_subscription_count() == 0 and time.monotonic() < end:
        rclpy.spin_once(node, timeout_sec=0.05)
    if pub.get_subscription_count() == 0:
        print(f"no subscriber on {pub.topic_name}; sending anyway", file=sys.stderr)


def walk(node, vx, vy, wz, secs):
    pub = node.create_publisher(Twist, os.environ.get("CMD_VEL_TOPIC", "/cmd_vel"), 10)
    wait_for_subscriber(node, pub)
    msg = Twist()
    msg.linear.x, msg.linear.y, msg.angular.z = vx, vy, wz
    end = time.monotonic() + secs
    while time.monotonic() < end:
        pub.publish(msg)
        time.sleep(1 / RATE_HZ)
    for _ in range(5):
        pub.publish(Twist())
        time.sleep(1 / RATE_HZ)


def press(node, buttons):
    pub = node.create_publisher(Joy, os.environ.get("JOY_TOPIC", "/joy"), 10)
    wait_for_subscriber(node, pub)
    for button in buttons:
        for down in (1, 0):
            msg = Joy()
            msg.header.stamp = node.get_clock().now().to_msg()
            msg.axes = JOY_AXES
            msg.buttons = [down if i == button else 0 for i in range(JOY_BUTTONS)]
            pub.publish(msg)
            time.sleep(0.2)


def main(argv):
    rclpy.init()
    node = rclpy.create_node("anti_tangping_cmd")
    try:
        if argv[0] == "walk":
            walk(node, *map(float, argv[1:5]))
        elif argv[0] == "press":
            press(node, [int(b) for b in argv[1:]])
        else:
            raise SystemExit(__doc__)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main(sys.argv[1:] or ["help"])
