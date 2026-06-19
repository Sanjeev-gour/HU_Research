#!/usr/bin/env python3

import rospy
import numpy as np
import torch
import torch.nn as nn
import joblib
import time

from ackermann_msgs.msg import AckermannDriveStamped
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry
from f110_msgs.msg import WpntArray
from tf.transformations import euler_from_quaternion
from scipy.spatial import KDTree


class MLController:

    def __init__(self):

        rospy.init_node('ml_controller', anonymous=True)

        self.loop_rate = 40
        self.LOOKAHEAD = 10
        self.velocity_scale = 0.92

        # Architecture must match training exactly
        self.model = nn.Sequential(
            nn.Linear(5, 64), nn.ReLU(), nn.Dropout(0.1),
            nn.Linear(64, 64), nn.ReLU(), nn.Dropout(0.1),
            nn.Linear(64, 32), nn.ReLU(),
            nn.Linear(32, 1)
        )

        model_path = "/home/sanjeev/f110_ws/src/ML_controller/models_path/model_method2V2_holdout_overtake.pth"
        self.model.load_state_dict(torch.load(model_path, weights_only=True))
        self.model.eval()  # disables dropout at inference time

        scaler_path = "/home/sanjeev/f110_ws/src/ML_controller/scaler_holdout_overtake.save"
        self.scaler = joblib.load(scaler_path)

        rospy.loginfo("Model and scaler loaded")

        # Warm up PyTorch to avoid latency spike on first inference
        dummy = torch.zeros(1, 5, dtype=torch.float32)
        for _ in range(200):
            with torch.no_grad():
                self.model(dummy)
        rospy.loginfo("PyTorch warmup done")

        self.position = None
        self.yaw = None
        self.vx = 0.0
        self.waypoints = None
        self.tree = None

        self.times = []
        self.counter = 0
        self.WARMUP_STEPS = 100

        self.drive_pub = rospy.Publisher(
            "/vesc/high_level/ackermann_cmd_mux/input/nav_1",
            AckermannDriveStamped,
            queue_size=10
        )

        rospy.Subscriber("/car_state/pose", PoseStamped, self.pose_cb)
        rospy.Subscriber("/car_state/odom", Odometry, self.odom_cb)
        rospy.Subscriber("/global_waypoints", WpntArray, self.wp_cb)

    def pose_cb(self, msg):
        x = msg.pose.position.x
        y = msg.pose.position.y
        q = msg.pose.orientation
        self.yaw = euler_from_quaternion([q.x, q.y, q.z, q.w])[2]
        self.position = np.array([x, y])

    def odom_cb(self, msg):
        self.vx = msg.twist.twist.linear.x

    def wp_cb(self, msg):
        if self.waypoints is None:
            self.waypoints = np.array([
                [wp.x_m, wp.y_m, wp.psi_rad, wp.kappa_radpm, wp.vx_mps]
                for wp in msg.wpnts
            ])
            self.tree = KDTree(self.waypoints[:, :2])
            rospy.loginfo("Waypoints loaded")

    def run(self):
        rate = rospy.Rate(self.loop_rate)

        while not rospy.is_shutdown():
            if self.position is None or self.tree is None:
                rate.sleep()
                continue

            x, y = self.position
            _, idx = self.tree.query([x, y])
            wp_x, wp_y, wp_yaw, kappa, wp_vx = self.waypoints[idx]

            # Signed lateral deviation: cross product gives left(+)/right(-) sign
            dx, dy = x - wp_x, y - wp_y
            cross = np.cross([np.cos(wp_yaw), np.sin(wp_yaw)], [dx, dy])
            d_m = np.sign(cross) * np.hypot(dx, dy)

            # arctan2 wraps the error to [-π, π]
            heading_error = np.arctan2(
                np.sin(self.yaw - wp_yaw),
                np.cos(self.yaw - wp_yaw)
            )

            kappa_la = self.waypoints[min(idx + self.LOOKAHEAD, len(self.waypoints) - 1)][3]

            features = self.scaler.transform(
                np.array([[d_m, heading_error, kappa, self.vx, kappa_la]])
            )
            features = torch.tensor(features, dtype=torch.float32)

            t0 = time.perf_counter()
            with torch.no_grad():
                steering = self.model(features).item()
            self.counter += 1
            if self.counter > self.WARMUP_STEPS:
                self.times.append((time.perf_counter() - t0) * 1000)
            if self.counter % 100 == 0 and self.times:
                rospy.loginfo(f"[ML] avg inference: {np.mean(self.times):.4f} ms")

            steering = np.clip(steering, -0.4, 0.4)
            speed = wp_vx * self.velocity_scale

            msg = AckermannDriveStamped()
            msg.header.stamp = rospy.Time.now()
            msg.header.frame_id = "base_link"
            msg.drive.steering_angle = steering
            msg.drive.speed = speed
            self.drive_pub.publish(msg)

            rate.sleep()


if __name__ == "__main__":
    controller = MLController()
    controller.run()
