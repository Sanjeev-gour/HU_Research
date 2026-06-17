#!/usr/bin/env python3

import rosbag
import numpy as np
import pandas as pd
from scipy.spatial import KDTree
from tf.transformations import euler_from_quaternion

# ===== CONFIG =====
BAG_PATH = "run_porto_0.825.bag"
LOOKAHEAD = 10   # number of waypoints ahead

# ===== LOAD BAG =====
bag = rosbag.Bag(BAG_PATH)

# ===== STORAGE =====
waypoints = []
odom_data = []
pose_data = []
control_data = []

# ===== READ BAG =====
for topic, msg, t in bag.read_messages():

    # ===== WAYPOINTS =====
    if topic == "/global_waypoints":
        for wp in msg.wpnts:
            waypoints.append([
                wp.x_m,
                wp.y_m,
                wp.psi_rad,
                wp.kappa_radpm,
                wp.vx_mps
            ])

    # ===== ODOM =====
    elif topic == "/car_state/odom":
        odom_data.append([
            t.to_sec(),
            msg.pose.pose.position.x,
            msg.pose.pose.position.y,
            msg.twist.twist.linear.x
        ])

    # ===== POSE =====
    elif topic == "/car_state/pose":
        quat = msg.pose.orientation
        yaw = euler_from_quaternion([
            quat.x, quat.y, quat.z, quat.w
        ])[2]

        pose_data.append([
            t.to_sec(),
            yaw
        ])

    # ===== CONTROL =====
    elif topic == "/vesc/high_level/ackermann_cmd_mux/input/nav_1":
        control_data.append([
            t.to_sec(),
            msg.drive.steering_angle
        ])

bag.close()

# ===== CONVERT TO NUMPY =====
waypoints = np.array(waypoints)
odom_data = np.array(odom_data)
pose_data = np.array(pose_data)
control_data = np.array(control_data)

print("Waypoints:", waypoints.shape)
print("Odom:", odom_data.shape)

# ===== KD-TREE FOR FAST NEAREST SEARCH =====
tree = KDTree(waypoints[:, :2])

# ===== HELPER: FIND NEAREST BY TIME =====
def find_nearest(data, t):
    idx = np.argmin(np.abs(data[:, 0] - t))
    return data[idx]

# ===== FEATURE EXTRACTION =====
dataset = []

for odom in odom_data:

    t, x, y, vx = odom

    # ===== MATCH POSE =====
    _, yaw = find_nearest(pose_data, t)

    # ===== MATCH CONTROL =====
    _, steering = find_nearest(control_data, t)

    # ===== NEAREST WAYPOINT =====
    dist, idx = tree.query([x, y])

    wp = waypoints[idx]

    wp_x, wp_y, wp_yaw, kappa, wp_vx = wp

    # ===== d_m =====
    dx = x - wp_x
    dy = y - wp_y
    d_m = np.sqrt(dx**2 + dy**2)

    # ===== SIGN OF d_m (LEFT/RIGHT) =====
    heading_vec = np.array([np.cos(wp_yaw), np.sin(wp_yaw)])
    error_vec = np.array([dx, dy])
    cross = np.cross(heading_vec, error_vec)
    d_m = np.sign(cross) * d_m

    # ===== HEADING ERROR =====
    heading_error = yaw - wp_yaw
    heading_error = np.arctan2(np.sin(heading_error), np.cos(heading_error))

    # ===== LOOKAHEAD KAPPA =====
    idx_la = min(idx + LOOKAHEAD, len(waypoints) - 1)
    kappa_la = waypoints[idx_la][3]

    # ===== STORE =====
    dataset.append([
        d_m,
        heading_error,
        kappa,
        vx,
        kappa_la,
        steering
    ])

# ===== SAVE CSV =====
df = pd.DataFrame(dataset, columns=[
    "d_m",
    "heading_error",
    "kappa",
    "vx",
    "kappa_lookahead",
    "steering"
])

df.to_csv("training_data_porto_0.825.csv", index=False)

print("✅ Dataset saved as training_data_porto_0.825.csv")
print("Total samples:", len(df))