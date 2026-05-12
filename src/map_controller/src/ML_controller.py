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

        # =============================================================
        # LOOP RATE
        # 40Hz = 25ms per loop | 100Hz = 10ms per loop
        # =============================================================
        self.loop_rate = 40

        # =============================================================
        # MODEL DEFINITION
        # Must match EXACTLY the architecture used during training
        # Now includes Dropout(0.2) — matches generalized training code
        # =============================================================
        class SteeringModel(nn.Module):
            def __init__(self):
                super(SteeringModel, self).__init__()

                self.net = nn.Sequential(
                    nn.Linear(5, 64),
                    nn.ReLU(),
                    nn.Dropout(0.2),      # must match training architecture

                    nn.Linear(64, 64),
                    nn.ReLU(),
                    nn.Dropout(0.2),      # must match training architecture

                    nn.Linear(64, 32),
                    nn.ReLU(),

                    nn.Linear(32, 1)
                )

            def forward(self, x):
                return self.net(x)

        # =============================================================
        # LOAD MODEL
        # Using best model (lowest val loss) not final epoch
        # =============================================================
        self.model = SteeringModel()
        model_path = "/home/sanjeev/f110_ws/src/ML_controller/model_generalized_best1.pth"
        self.model.load_state_dict(torch.load(model_path))

        # IMPORTANT: model.eval() disables Dropout during inference
        # Without this, Dropout stays active and predictions are random
        self.model.eval()

        # =============================================================
        # LOAD SCALER
        # Must use scaler_generalized.save — fitted on all 4 maps
        # Old scaler.save was fitted on single map — DO NOT USE
        # =============================================================
        scaler_path = "/home/sanjeev/f110_ws/src/ML_controller/scaler_generalized.save"
        self.scaler = joblib.load(scaler_path)

        rospy.loginfo("✅ Generalized Model + Scaler Loaded")

        # =============================================================
        # INFERENCE TIME TRACKING
        # Logs average every 100 steps to monitor real-time performance
        # =============================================================
        self.times   = []
        self.counter = 0

        # =============================================================
        # STATE VARIABLES
        # =============================================================
        self.position  = None   # [x, y] in map frame
        self.yaw       = None   # heading angle in radians
        self.vx        = 0.0   # current speed from odometry

        self.waypoints = None   # global waypoints [x, y, psi, kappa, vx]
        self.tree      = None   # KDTree for fast nearest waypoint lookup

        # =============================================================
        # PARAMETERS
        # LOOKAHEAD: number of waypoints ahead for kappa_lookahead
        # velocity_scale: scale factor applied to waypoint speed
        # =============================================================
        self.LOOKAHEAD      = 10
        self.velocity_scale = 0.825

        # =============================================================
        # PUBLISHER
        # Publishes AckermannDriveStamped to the drive mux
        # =============================================================
        self.drive_pub = rospy.Publisher(
            "/vesc/high_level/ackermann_cmd_mux/input/nav_1",
            AckermannDriveStamped,
            queue_size=10
        )

        # =============================================================
        # SUBSCRIBERS
        # pose  → position and heading of the car
        # odom  → current speed of the car
        # waypoints → global racing line waypoints
        # =============================================================
        rospy.Subscriber("/car_state/pose",      PoseStamped,  self.pose_cb)
        rospy.Subscriber("/car_state/odom",      Odometry,     self.odom_cb)
        rospy.Subscriber("/global_waypoints",    WpntArray,    self.wp_cb)

    # =============================================================
    # CALLBACK: POSE
    # Extracts x, y position and yaw from quaternion
    # =============================================================
    def pose_cb(self, msg):
        x   = msg.pose.position.x
        y   = msg.pose.position.y
        quat = msg.pose.orientation
        yaw = euler_from_quaternion([quat.x, quat.y, quat.z, quat.w])[2]

        self.position = np.array([x, y])
        self.yaw      = yaw

    # =============================================================
    # CALLBACK: ODOMETRY
    # Gets current forward speed of the car
    # =============================================================
    def odom_cb(self, msg):
        self.vx = msg.twist.twist.linear.x

    # =============================================================
    # CALLBACK: WAYPOINTS
    # Loads waypoints once and builds KDTree for fast lookup
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
            self.tree      = KDTree(self.waypoints[:, :2])
            rospy.loginfo("✅ Waypoints loaded")

    # =============================================================
    # MAIN CONTROL LOOP
    # =============================================================
    def run(self):

        rate = rospy.Rate(self.loop_rate)

        while not rospy.is_shutdown():

            # Wait until pose and waypoints are available
            if self.position is None or self.waypoints is None:
                rate.sleep()
                continue

            x, y = self.position

            # =============================================================
            # NEAREST WAYPOINT
            # KDTree query is O(log n) — fast enough for 40/100Hz
            # =============================================================
            _, idx = self.tree.query([x, y])
            wp = self.waypoints[idx]
            wp_x, wp_y, wp_yaw, kappa, wp_vx = wp

            # =============================================================
            # FEATURE 1: d_m — signed lateral deviation from racing line
            # Positive = car is to the left of path
            # Negative = car is to the right of path
            # =============================================================
            dx    = x - wp_x
            dy    = y - wp_y
            d_m   = np.sqrt(dx**2 + dy**2)

            heading_vec = np.array([np.cos(wp_yaw), np.sin(wp_yaw)])
            error_vec   = np.array([dx, dy])
            cross       = np.cross(heading_vec, error_vec)
            d_m         = np.sign(cross) * d_m

            # =============================================================
            # FEATURE 2: heading_error — angle between car and path
            # arctan2 wraps the angle to [-pi, pi]
            # =============================================================
            heading_error = self.yaw - wp_yaw
            heading_error = np.arctan2(np.sin(heading_error), np.cos(heading_error))

            # =============================================================
            # FEATURE 3: kappa — curvature at nearest waypoint
            # FEATURE 4: vx — current car speed
            # FEATURE 5: kappa_lookahead — curvature 10 waypoints ahead
            # min() prevents index out of bounds at end of waypoint array
            # =============================================================
            idx_la   = min(idx + self.LOOKAHEAD, len(self.waypoints) - 1)
            kappa_la = self.waypoints[idx_la][3]

            # =============================================================
            # BUILD AND SCALE FEATURE VECTOR
            # scaler_generalized was fitted on all 4 maps — use this only
            # =============================================================
            features = np.array([[d_m, heading_error, kappa, self.vx, kappa_la]])
            features = self.scaler.transform(features)
            features = torch.tensor(features, dtype=torch.float32)

            # =============================================================
            # INFERENCE
            # torch.no_grad() disables gradient tracking — faster inference
            # model.eval() already set in __init__ — Dropout is disabled
            # =============================================================
            start_time = time.perf_counter()

            with torch.no_grad():
                steering = self.model(features).item()

            end_time       = time.perf_counter()
            inference_time = (end_time - start_time) * 1000  # convert to ms

            # =============================================================
            # INFERENCE TIME LOGGING
            # Prints average every 100 steps
            # =============================================================
            self.times.append(inference_time)
            self.counter += 1

            if self.counter % 100 == 0:
                avg_time = np.mean(self.times)
                rospy.loginfo(f"[Generalized ML] Avg Inference Time: {avg_time:.4f} ms")

            # =============================================================
            # SAFETY CLIPPING
            # Hard limit on steering — protects hardware
            # =============================================================
            steering = np.clip(steering, -0.4, 0.4)

            # =============================================================
            # SPEED
            # Uses waypoint target speed scaled by velocity_scale
            # =============================================================
            speed = wp_vx * self.velocity_scale

            # =============================================================
            # PUBLISH DRIVE COMMAND
            # =============================================================
            msg = AckermannDriveStamped()
            msg.header.stamp    = rospy.Time.now()
            msg.header.frame_id = "base_link"

            msg.drive.steering_angle = steering
            msg.drive.speed          = speed

            self.drive_pub.publish(msg)

            rate.sleep()


if __name__ == "__main__":
    controller = MLController()
    controller.run()