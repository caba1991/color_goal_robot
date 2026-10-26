#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from std_msgs.msg import String


GOALS = {
    "red": (2.0, 0.0),
    "blue": (0.0, 2.0),
    "green": (-2.0, 0.0),
}


class MoveToGoal(Node):

    def __init__(self):
        super().__init__("move_to_goal")

        self.cmd_pub = self.create_publisher(
            Twist,
            "/cmd_vel",
            10
        )

        self.odom_sub = self.create_subscription(
            Odometry,
            "/odom",
            self.odom_callback,
            10
        )

        self.goal_sub = self.create_subscription(
            String,
            "/target_color",
            self.target_callback,
            10
        )

        self.timer = self.create_timer(
            0.1,
            self.control_loop
        )

        self.x = 0.0
        self.y = 0.0
        self.yaw = 0.0
        self.target = None

    def odom_callback(self, msg):
        self.x = msg.pose.pose.position.x
        self.y = msg.pose.pose.position.y

        q = msg.pose.pose.orientation

        sin_yaw = 2.0 * (q.w * q.z + q.x * q.y)
        cos_yaw = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)

        self.yaw = math.atan2(sin_yaw, cos_yaw)

    def target_callback(self, msg):
        color = msg.data.strip().lower()

        if color not in GOALS:
            self.get_logger().error(
                f"Unknown target: {color}"
            )
            self.target = None
            self.stop_robot()
            return

        self.target = GOALS[color]

        self.get_logger().info(
            f"Target received: {color}, {self.target}"
        )

    def stop_robot(self):
        cmd = Twist()
        self.cmd_pub.publish(cmd)

    def control_loop(self):
        if self.target is None:
            self.stop_robot()
            return

        target_x, target_y = self.target

        dx = target_x - self.x
        dy = target_y - self.y

        distance = math.sqrt(dx * dx + dy * dy)

        target_yaw = math.atan2(dy, dx)
        angle_error = target_yaw - self.yaw

        angle_error = math.atan2(
            math.sin(angle_error),
            math.cos(angle_error)
        )

        cmd = Twist()

        if distance < 0.2:
            self.get_logger().info("Goal reached")
            self.target = None
            self.stop_robot()
            return

        if abs(angle_error) > 0.25:
            cmd.linear.x = 0.0
            cmd.angular.z = 0.6 if angle_error > 0 else -0.6
        else:
            cmd.linear.x = min(0.25, 0.5 * distance)
            cmd.angular.z = 0.8 * angle_error

        self.cmd_pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)

    node = MoveToGoal()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass

    node.stop_robot()
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
