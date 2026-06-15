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

        # LOOP RATE
        self.loop_rate = 40

        # MODEL DEFINITION
        # MUST MATCH TRAINING ARCHITECTURE EXACTLY
        self.model = nn.Sequential(

            nn.Linear(5, 64),
            nn.ReLU(),
            nn.Dropout(0.1),

            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Dropout(0.1),

            nn.Linear(64, 32),
            nn.ReLU(),

            nn.Linear(32, 1)
        )

        # =============================================================
        # LOAD MODEL
        # =============================================================
        model_path = "/home/sanjeev/f110_ws/src/ML_controller/models_path/ml_model_relu_best.pth"

        self.model.load_state_dict(torch.load(model_path))

        # IMPORTANT: disables dropout during inference
        self.model.eval()

        # =============================================================
        # LOAD SCALER
        # =============================================================
        scaler_path = "/home/sanjeev/f110_ws/src/ML_controller/scaler_generalized.save"
        self.scaler = joblib.load(scaler_path)

        rospy.loginfo("✅ Generalized Model + Scaler Loaded")

        # =============================================================
        # PYTORCH WARMUP
        # =============================================================
        rospy.loginfo("🔥 Warming up PyTorch...")

        dummy_input = torch.zeros(1, 5, dtype=torch.float32)

        for _ in range(200):
            with torch.no_grad():
                _ = self.model(dummy_input)

        rospy.loginfo("✅ PyTorch warmup complete")

        # =============================================================
        # INFERENCE TIME TRACKING
        # =============================================================
        self.times = []
        self.counter = 0
        self.WARMUP_STEPS = 100

        # =============================================================
        # STATE VARIABLES
        # =============================================================
        self.position = None
        self.yaw = None
        self.vx = 0.0

        self.waypoints = None
        self.tree = None


        # =============================================================
        # PARAMETERS
        # =============================================================
        self.LOOKAHEAD = 10
        self.velocity_scale = 0.825

        # =============================================================
        # PUBLISHER
        # =============================================================
        self.drive_pub = rospy.Publisher(
            "/vesc/high_level/ackermann_cmd_mux/input/nav_1",
            AckermannDriveStamped,
            queue_size=10
        )

        # =============================================================
        # SUBSCRIBERS
        # =============================================================
        rospy.Subscriber("/car_state/pose", PoseStamped, self.pose_cb)
        rospy.Subscriber("/car_state/odom", Odometry, self.odom_cb)
        rospy.Subscriber("/global_waypoints", WpntArray, self.wp_cb)

    # =============================================================
    # POSE CALLBACK
    # =============================================================
    def pose_cb(self, msg):

        x = msg.pose.position.x
        y = msg.pose.position.y

        quat = msg.pose.orientation

        yaw = euler_from_quaternion([
            quat.x,
            quat.y,
            quat.z,
            quat.w
        ])[2]

        self.position = np.array([x, y])
        self.yaw = yaw

    # =============================================================
    # ODOM CALLBACK
    # =============================================================
    def odom_cb(self, msg):

        self.vx = msg.twist.twist.linear.x

    # =============================================================
    # WAYPOINT CALLBACK
    # =============================================================
    def wp_cb(self, msg):

        if self.waypoints is None:

            wp_list = []

            for wp in msg.wpnts:

                wp_list.append([
                    wp.x_m,
                    wp.y_m,
                    wp.psi_rad,
                    wp.kappa_radpm,
                    wp.vx_mps
                ])

            self.waypoints = np.array(wp_list)

            self.tree = KDTree(self.waypoints[:, :2])

            rospy.loginfo("✅ Waypoints loaded")

    # =============================================================
    # MAIN CONTROL LOOP
    # =============================================================
    def run(self):

        rate = rospy.Rate(self.loop_rate)

        while not rospy.is_shutdown():

            if self.position is None or self.waypoints is None:
                rate.sleep()
                continue

            x, y = self.position

            # =============================================================
            # NEAREST WAYPOINT
            # =============================================================
            _, idx = self.tree.query([x, y])

            wp = self.waypoints[idx]

            wp_x, wp_y, wp_yaw, kappa, wp_vx = wp

            # =============================================================
            # d_m (SIGNED LATERAL ERROR)
            # =============================================================
            dx = x - wp_x
            dy = y - wp_y

            d_m = np.sqrt(dx**2 + dy**2)

            heading_vec = np.array([
                np.cos(wp_yaw),
                np.sin(wp_yaw)
            ])

            error_vec = np.array([dx, dy])

            cross = np.cross(heading_vec, error_vec)

            d_m = np.sign(cross) * d_m

            # =============================================================
            # HEADING ERROR
            # =============================================================
            heading_error = self.yaw - wp_yaw

            heading_error = np.arctan2(
                np.sin(heading_error),
                np.cos(heading_error)
            )

            # =============================================================
            # LOOKAHEAD CURVATURE
            # =============================================================
            idx_la = min(
                idx + self.LOOKAHEAD,
                len(self.waypoints) - 1
            )

            kappa_la = self.waypoints[idx_la][3]

            # =============================================================
            # FEATURE VECTOR
            # =============================================================
            features = np.array([[
                d_m,
                heading_error,
                kappa,
                self.vx,
                kappa_la
            ]])

            # =============================================================
            # SCALE FEATURES
            # =============================================================
            features = self.scaler.transform(features)

            features = torch.tensor(
                features,
                dtype=torch.float32
            )

            # =============================================================
            # MODEL INFERENCE
            # =============================================================
            start_time = time.perf_counter()

            with torch.no_grad():
                steering = self.model(features).item()

            end_time = time.perf_counter()

            inference_time = (end_time - start_time) * 1000

            # =============================================================
            # INFERENCE TIME TRACKING
            # =============================================================
            self.counter += 1

            if self.counter > self.WARMUP_STEPS:
                self.times.append(inference_time)

            if self.counter % 100 == 0:

                if len(self.times) > 0:

                    avg_time = np.mean(self.times)

                    rospy.loginfo(
                        f"[Generalized ML] Avg Inference Time: {avg_time:.4f} ms"
                    )

                else:
                    rospy.loginfo(
                        f"[Generalized ML] Warming up... step {self.counter}"
                    )

            # =============================================================
            # SAFETY CLIPPING
            # =============================================================
            steering = np.clip(steering, -0.4, 0.4)

            # =============================================================
            # SPEED
            # =============================================================
            speed = wp_vx * self.velocity_scale

            # =============================================================
            # PUBLISH COMMAND
            # =============================================================
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