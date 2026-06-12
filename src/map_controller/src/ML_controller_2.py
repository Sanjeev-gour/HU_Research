#!/usr/bin/env python3

#!/usr/bin/env python3

import rospy
import numpy as np
import torch
import time
import joblib

from ackermann_msgs.msg import AckermannDriveStamped
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry
from f110_msgs.msg import WpntArray
from tf.transformations import euler_from_quaternion
from scipy.spatial import KDTree


# =============================================================
# ELM MODEL CLASS
# MUST MATCH TRAINING FILE EXACTLY
# =============================================================

class ELMRegressor:

    def __init__(
        self,
        input_size,
        hidden_size=128,
        activation='relu'
    ):

        self.input_size = input_size
        self.hidden_size = hidden_size
        self.activation = activation

        self.W = None
        self.b = None
        self.beta = None

    # =========================================================
    # ACTIVATION FUNCTION
    # =========================================================

    def _activate(self, X):

        H = np.dot(X, self.W) + self.b

        if self.activation == 'relu':
            return np.maximum(0, H)

        elif self.activation == 'tanh':
            return np.tanh(H)

        elif self.activation == 'sigmoid':
            return 1 / (1 + np.exp(-H))

        else:
            raise ValueError("Unsupported activation")

    # =========================================================
    # PREDICTION
    # =========================================================

    def predict(self, X):

        H = self._activate(X)

        return H @ self.beta


# =============================================================
# CONTROLLER
# =============================================================

class ELMController:

    def __init__(self):

        rospy.init_node('ml_controller_2', anonymous=True)

        # =====================================================
        # PARAMETERS
        # =====================================================

        self.loop_rate = 40
        self.LOOKAHEAD = 10
        self.velocity_scale = 0.9

        # =====================================================
        # LOAD ELM MODEL
        # =====================================================

        model_path = "/home/sanjeev/f110_ws/src/ML_controller/models_path/model_elm.pth"

        rospy.loginfo("Loading ELM model...")

        self.model = torch.load(
            model_path,
            weights_only=False
        )

        rospy.loginfo("✅ ELM model loaded")

        # =====================================================
        # LOAD GENERALIZED SCALER
        # =====================================================

        scaler_path = "/home/sanjeev/f110_ws/src/ML_controller/scaler_generalized.save"

        self.scaler = joblib.load(scaler_path)

        rospy.loginfo("✅ Scaler loaded")

        # =====================================================
        # STATE VARIABLES
        # =====================================================

        self.position = None
        self.yaw = None
        self.vx = 0.0

        self.waypoints = None
        self.tree = None

        # =====================================================
        # TIMING
        # =====================================================

        self.times = []
        self.counter = 0
        self.WARMUP_STEPS = 100

        # =====================================================
        # PUBLISHER
        # =====================================================

        self.drive_pub = rospy.Publisher(
            "/vesc/high_level/ackermann_cmd_mux/input/nav_1",
            AckermannDriveStamped,
            queue_size=10
        )

        # =====================================================
        # SUBSCRIBERS
        # =====================================================

        rospy.Subscriber(
            "/car_state/pose",
            PoseStamped,
            self.pose_cb
        )

        rospy.Subscriber(
            "/car_state/odom",
            Odometry,
            self.odom_cb
        )

        rospy.Subscriber(
            "/global_waypoints",
            WpntArray,
            self.wp_cb
        )

    # =========================================================
    # POSE CALLBACK
    # =========================================================

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

    # =========================================================
    # ODOM CALLBACK
    # =========================================================

    def odom_cb(self, msg):

        self.vx = msg.twist.twist.linear.x

    # =========================================================
    # WAYPOINT CALLBACK
    # =========================================================

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

            self.tree = KDTree(
                self.waypoints[:, :2]
            )

            rospy.loginfo("✅ Waypoints loaded")

    # =========================================================
    # MAIN LOOP
    # =========================================================

    def run(self):

        rate = rospy.Rate(self.loop_rate)

        while not rospy.is_shutdown():

            if self.position is None or self.waypoints is None:

                rate.sleep()
                continue

            x, y = self.position

            # =================================================
            # NEAREST WAYPOINT
            # =================================================

            _, idx = self.tree.query([x, y])

            wp = self.waypoints[idx]

            wp_x, wp_y, wp_yaw, kappa, wp_vx = wp

            # =================================================
            # SIGNED LATERAL ERROR
            # =================================================

            dx = x - wp_x
            dy = y - wp_y

            d_m = np.sqrt(dx**2 + dy**2)

            heading_vec = np.array([
                np.cos(wp_yaw),
                np.sin(wp_yaw)
            ])

            error_vec = np.array([dx, dy])

            cross = np.cross(
                heading_vec,
                error_vec
            )

            d_m = np.sign(cross) * d_m

            # =================================================
            # HEADING ERROR
            # =================================================

            heading_error = self.yaw - wp_yaw

            heading_error = np.arctan2(
                np.sin(heading_error),
                np.cos(heading_error)
            )

            # =================================================
            # LOOKAHEAD CURVATURE
            # =================================================

            idx_la = min(
                idx + self.LOOKAHEAD,
                len(self.waypoints) - 1
            )

            kappa_la = self.waypoints[idx_la][3]

            # =================================================
            # FEATURE VECTOR
            # =================================================

            features = np.array([[
                d_m,
                heading_error,
                kappa,
                self.vx,
                kappa_la
            ]])

            # =================================================
            # SCALE FEATURES
            # =================================================

            features_scaled = self.scaler.transform(
                features
            )

            # =================================================
            # MODEL INFERENCE
            # =================================================

            start_time = time.perf_counter()

            steering = self.model.predict(
                features_scaled
            )[0]

            end_time = time.perf_counter()

            inference_time = (
                (end_time - start_time) * 1000
            )

            # =================================================
            # TIMING STATS
            # =================================================

            self.counter += 1

            if self.counter > self.WARMUP_STEPS:

                self.times.append(inference_time)

            if self.counter % 100 == 0:

                avg_time = np.mean(self.times)

                rospy.loginfo(
                    f"[ELM] Avg Inference: "
                    f"{avg_time:.6f} ms"
                )

            # =================================================
            # SAFETY CLIP
            # =================================================

            steering = np.clip(
                steering,
                -0.4,
                0.4
            )

            # =================================================
            # SPEED
            # =================================================

            speed = wp_vx * self.velocity_scale

            # =================================================
            # PUBLISH COMMAND
            # =================================================

            msg = AckermannDriveStamped()

            msg.header.stamp = rospy.Time.now()

            msg.header.frame_id = "base_link"

            msg.drive.steering_angle = steering

            msg.drive.speed = speed

            self.drive_pub.publish(msg)

            rate.sleep()


# =============================================================
# MAIN
# =============================================================

if __name__ == "__main__":

    controller = ELMController()

    controller.run()

# import rospy
# import numpy as np
# import time
# import joblib

# from ackermann_msgs.msg import AckermannDriveStamped
# from geometry_msgs.msg import PoseStamped
# from nav_msgs.msg import Odometry
# from f110_msgs.msg import WpntArray
# from tf.transformations import euler_from_quaternion
# from scipy.spatial import KDTree


# class ClassicalMLController:

#     def __init__(self):

#         rospy.init_node('ml_controller_2', anonymous=True)

#         # =============================================================
#         # PARAMETERS
#         # =============================================================
#         self.loop_rate = 40
#         self.LOOKAHEAD = 10
#         self.velocity_scale = 0.825

#         # =============================================================
#         # LOAD MODEL
#         # =============================================================

#         model_path = "/home/sanjeev/f110_ws/src/ML_controller/models_path/model_gp.pth"

#         rospy.loginfo("Loading Classical ML model...")

#         # FIXED HERE
#         self.model = joblib.load(model_path)

#         rospy.loginfo("✅ Model loaded")

#         # =============================================================
#         # LOAD SCALER
#         # =============================================================

#         scaler_path = "/home/sanjeev/f110_ws/src/ML_controller/scaler_generalized.save"

#         self.scaler = joblib.load(scaler_path)

#         rospy.loginfo("✅ Scaler loaded")

#         # =============================================================
#         # STATE VARIABLES
#         # =============================================================

#         self.position = None
#         self.yaw = None
#         self.vx = 0.0

#         self.waypoints = None
#         self.tree = None

#         # =============================================================
#         # TIMING
#         # =============================================================

#         self.times = []
#         self.counter = 0
#         self.WARMUP_STEPS = 100

#         # =============================================================
#         # PUBLISHER
#         # =============================================================

#         self.drive_pub = rospy.Publisher(
#             "/vesc/high_level/ackermann_cmd_mux/input/nav_1",
#             AckermannDriveStamped,
#             queue_size=10
#         )

#         # =============================================================
#         # SUBSCRIBERS
#         # =============================================================

#         rospy.Subscriber(
#             "/car_state/pose",
#             PoseStamped,
#             self.pose_cb
#         )

#         rospy.Subscriber(
#             "/car_state/odom",
#             Odometry,
#             self.odom_cb
#         )

#         rospy.Subscriber(
#             "/global_waypoints",
#             WpntArray,
#             self.wp_cb
#         )

#     # =============================================================
#     # POSE CALLBACK
#     # =============================================================

#     def pose_cb(self, msg):

#         x = msg.pose.position.x
#         y = msg.pose.position.y

#         quat = msg.pose.orientation

#         yaw = euler_from_quaternion([
#             quat.x,
#             quat.y,
#             quat.z,
#             quat.w
#         ])[2]

#         self.position = np.array([x, y])
#         self.yaw = yaw

#     # =============================================================
#     # ODOM CALLBACK
#     # =============================================================

#     def odom_cb(self, msg):

#         self.vx = msg.twist.twist.linear.x

#     # =============================================================
#     # WAYPOINT CALLBACK
#     # =============================================================

#     def wp_cb(self, msg):

#         if self.waypoints is None:

#             wp_list = []

#             for wp in msg.wpnts:

#                 wp_list.append([
#                     wp.x_m,
#                     wp.y_m,
#                     wp.psi_rad,
#                     wp.kappa_radpm,
#                     wp.vx_mps
#                 ])

#             self.waypoints = np.array(wp_list)

#             self.tree = KDTree(self.waypoints[:, :2])

#             rospy.loginfo("✅ Waypoints loaded")

#     # =============================================================
#     # MAIN LOOP
#     # =============================================================

#     def run(self):

#         rate = rospy.Rate(self.loop_rate)

#         while not rospy.is_shutdown():

#             if self.position is None or self.waypoints is None:
#                 rate.sleep()
#                 continue

#             x, y = self.position

#             # =============================================================
#             # NEAREST WAYPOINT
#             # =============================================================

#             _, idx = self.tree.query([x, y])

#             wp = self.waypoints[idx]

#             wp_x, wp_y, wp_yaw, kappa, wp_vx = wp

#             # =============================================================
#             # LATERAL ERROR
#             # =============================================================

#             dx = x - wp_x
#             dy = y - wp_y

#             d_m = np.sqrt(dx**2 + dy**2)

#             heading_vec = np.array([
#                 np.cos(wp_yaw),
#                 np.sin(wp_yaw)
#             ])

#             error_vec = np.array([dx, dy])

#             cross = np.cross(heading_vec, error_vec)

#             d_m = np.sign(cross) * d_m

#             # =============================================================
#             # HEADING ERROR
#             # =============================================================

#             heading_error = self.yaw - wp_yaw

#             heading_error = np.arctan2(
#                 np.sin(heading_error),
#                 np.cos(heading_error)
#             )

#             # =============================================================
#             # LOOKAHEAD CURVATURE
#             # =============================================================

#             idx_la = min(
#                 idx + self.LOOKAHEAD,
#                 len(self.waypoints) - 1
#             )

#             kappa_la = self.waypoints[idx_la][3]

#             # =============================================================
#             # FEATURE VECTOR
#             # =============================================================

#             features = np.array([[
#                 d_m,
#                 heading_error,
#                 kappa,
#                 self.vx,
#                 kappa_la
#             ]])

#             # =============================================================
#             # SCALE FEATURES
#             # =============================================================

#             features_scaled = self.scaler.transform(features)

#             # =============================================================
#             # MODEL INFERENCE
#             # =============================================================

#             start_time = time.perf_counter()

#             steering = self.model.predict(features_scaled)[0]

#             end_time = time.perf_counter()

#             inference_time = (end_time - start_time) * 1000

#             # =============================================================
#             # TIMING LOG
#             # =============================================================

#             self.counter += 1

#             if self.counter > self.WARMUP_STEPS:
#                 self.times.append(inference_time)

#             if self.counter % 100 == 0:

#                 if len(self.times) > 0:

#                     avg_time = np.mean(self.times)

#                     rospy.loginfo(
#                         f"[Classical ML] Avg inference: {avg_time:.4f} ms"
#                     )

#             # =============================================================
#             # SAFETY CLIP
#             # =============================================================

#             steering = np.clip(steering, -0.4, 0.4)

#             # =============================================================
#             # SPEED
#             # =============================================================

#             speed = wp_vx * self.velocity_scale

#             # =============================================================
#             # PUBLISH
#             # =============================================================

#             msg = AckermannDriveStamped()

#             msg.header.stamp = rospy.Time.now()
#             msg.header.frame_id = "base_link"

#             msg.drive.steering_angle = steering
#             msg.drive.speed = speed

#             self.drive_pub.publish(msg)

#             rate.sleep()


# if __name__ == "__main__":

#     controller = ClassicalMLController()

#     controller.run()