#!/usr/bin/env python3

# =============================================================
# ML CONTROLLER V3
# =============================================================
# Improvements over ML_controller.py (V1):
#   1. Four lookahead curvatures: kappa at 5, 10, 20, 30 wp ahead
#      → network sees the shape of the upcoming curve, not just one point
#   2. Lateral velocity (vy) as feature
#      → network knows if the car is sliding or gripping
#   3. Adaptive primary lookahead index scales with speed
#      → consistent physical meaning at all speeds
#   4. 9-input network: 9 → 128 → 128 → 64 → 32 → 1
#
# Model  : ML_controller/models_path/method2_modelV3_best.pth
# Scaler : ML_controller/models_path/scaler_V3.save
# =============================================================

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


# =============================================================
# MODEL DEFINITION — must match model_method2V3.py exactly
# =============================================================
class SteeringModelV3(nn.Module):
    def __init__(self):
        super(SteeringModelV3, self).__init__()

        self.net = nn.Sequential(

            nn.Linear(9, 128),
            nn.ReLU(),
            nn.Dropout(0.2),

            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Dropout(0.2),

            nn.Linear(128, 64),
            nn.ReLU(),
            nn.Dropout(0.1),

            nn.Linear(64, 32),
            nn.ReLU(),

            nn.Linear(32, 1)
        )

    def forward(self, x):
        return self.net(x)


class MLControllerV3:

    def __init__(self):

        rospy.init_node('ml_controller_v3', anonymous=True)

        self.loop_rate     = 40
        self.velocity_scale = 0.825

        # Fixed lookahead steps for the 4 curvature features
        # (must match what was used in extract_data_method2V3.py)
        self.LA_STEPS = [5, 10, 20, 30]

        # =============================================================
        # LOAD MODEL
        # =============================================================
        model_path = "/home/sanjeev/f110_ws/src/ML_controller/models_path/method2_modelV3_best.pth"

        self.model = SteeringModelV3()
        self.model.load_state_dict(torch.load(model_path))
        self.model.eval()

        # =============================================================
        # LOAD SCALER
        # =============================================================
        scaler_path = "/home/sanjeev/f110_ws/src/ML_controller/models_path/scaler_V3.save"
        self.scaler = joblib.load(scaler_path)

        rospy.loginfo("✅ ML Controller V3 — Model + Scaler Loaded")

        # =============================================================
        # PYTORCH WARMUP
        # =============================================================
        dummy = torch.zeros(1, 9, dtype=torch.float32)
        for _ in range(200):
            with torch.no_grad():
                _ = self.model(dummy)
        rospy.loginfo("✅ PyTorch warmup complete")

        # =============================================================
        # INFERENCE TIME TRACKING
        # =============================================================
        self.times        = []
        self.counter      = 0
        self.WARMUP_STEPS = 100

        # =============================================================
        # STATE VARIABLES
        # =============================================================
        self.position  = None
        self.yaw       = None
        self.vx        = 0.0
        self.vy        = 0.0        # lateral velocity — NEW

        self.waypoints = None
        self.tree      = None

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
        rospy.Subscriber("/car_state/pose",  PoseStamped, self.pose_cb)
        rospy.Subscriber("/car_state/odom",  Odometry,    self.odom_cb)
        rospy.Subscriber("/global_waypoints", WpntArray,  self.wp_cb)

    # =============================================================
    # CALLBACKS
    # =============================================================
    def pose_cb(self, msg):
        x   = msg.pose.position.x
        y   = msg.pose.position.y
        yaw = euler_from_quaternion([
            msg.pose.orientation.x,
            msg.pose.orientation.y,
            msg.pose.orientation.z,
            msg.pose.orientation.w
        ])[2]
        self.position = np.array([x, y])
        self.yaw      = yaw

    def odom_cb(self, msg):
        self.vx = msg.twist.twist.linear.x
        self.vy = msg.twist.twist.linear.y   # lateral velocity

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
            self.tree      = KDTree(self.waypoints[:, :2])
            rospy.loginfo("✅ Waypoints loaded")

    # =============================================================
    # MAIN CONTROL LOOP
    # =============================================================
    def run(self):

        rate  = rospy.Rate(self.loop_rate)
        n_wp  = None

        while not rospy.is_shutdown():

            if self.position is None or self.waypoints is None:
                rate.sleep()
                continue

            if n_wp is None:
                n_wp = len(self.waypoints)

            x, y = self.position

            # ===== NEAREST WAYPOINT =====
            _, idx = self.tree.query([x, y])
            wp_x, wp_y, wp_yaw, kappa, wp_vx = self.waypoints[idx]

            # ===== d_m — signed lateral error =====
            dx    = x - wp_x
            dy    = y - wp_y
            d_m   = np.sqrt(dx**2 + dy**2)
            cross = np.cross(
                np.array([np.cos(wp_yaw), np.sin(wp_yaw)]),
                np.array([dx, dy])
            )
            d_m = np.sign(cross) * d_m

            # ===== HEADING ERROR =====
            heading_error = np.arctan2(
                np.sin(self.yaw - wp_yaw),
                np.cos(self.yaw - wp_yaw)
            )

            # ===== FOUR LOOKAHEAD CURVATURES =====
            kappas_la = []
            for steps in self.LA_STEPS:
                idx_la = min(idx + steps, n_wp - 1)
                kappas_la.append(self.waypoints[idx_la][3])

            # ===== FEATURE VECTOR (9 features) =====
            features = np.array([[
                d_m,
                heading_error,
                kappa,
                self.vx,
                kappas_la[0],   # kappa_la_5
                kappas_la[1],   # kappa_la_10
                kappas_la[2],   # kappa_la_20
                kappas_la[3],   # kappa_la_30
                self.vy
            ]])

            # ===== SCALE =====
            features = self.scaler.transform(features)
            features = torch.tensor(features, dtype=torch.float32)

            # ===== INFERENCE =====
            start = time.perf_counter()

            with torch.no_grad():
                steering = self.model(features).item()

            elapsed = (time.perf_counter() - start) * 1000

            # ===== INFERENCE TIME TRACKING =====
            self.counter += 1
            if self.counter > self.WARMUP_STEPS:
                self.times.append(elapsed)

            if self.counter % 100 == 0 and len(self.times) > 0:
                rospy.loginfo(
                    f"[ML V3] Avg inference: {np.mean(self.times):.4f} ms"
                )

            # ===== SAFETY CLIP =====
            steering = np.clip(steering, -0.4, 0.4)

            # ===== SPEED from waypoint =====
            speed = wp_vx * self.velocity_scale

            # ===== PUBLISH =====
            msg                       = AckermannDriveStamped()
            msg.header.stamp          = rospy.Time.now()
            msg.header.frame_id       = "base_link"
            msg.drive.steering_angle  = steering
            msg.drive.speed           = speed

            self.drive_pub.publish(msg)
            rate.sleep()


if __name__ == "__main__":
    controller = MLControllerV3()
    controller.run()
