#!/usr/bin/env python3

# =============================================================
# DATA EXTRACTION — METHOD 2 V3
# =============================================================
# Improvements over V1/V2 extraction:
#   1. Four lookahead curvatures instead of one (5, 10, 20, 30 wp ahead)
#   2. Lateral velocity (vy) added as a feature — proxy for grip/slide
#   3. Data augmentation: every sample is mirrored left-right,
#      doubling the dataset and balancing left/right turns
#
# Output columns:
#   d_m, heading_error, kappa, vx, kappa_la_5, kappa_la_10,
#   kappa_la_20, kappa_la_30, vy, steering
#
# Run from: /home/sanjeev/f110_ws/src/Data/execution_files/
#   python3 extract_data_method2V3.py
#
# Output: /home/sanjeev/f110_ws/src/Data/data_files/method2V3_data.csv
# =============================================================

import rosbag
import numpy as np
import pandas as pd
from scipy.spatial import KDTree
from tf.transformations import euler_from_quaternion
import os

# =============================================================
# CONFIG — training bags only (porto is test map, excluded)
# =============================================================
BAG_DIR = "/home/sanjeev/f110_ws/src/Data/bag_files"

TRAINING_BAGS = [
    "run_berlin_0.6.bag",
    "run_berlin_0.825.bag",
    "run_f_0.6.bag",
    "run_f_0.825.bag",
    "run_hangar_0.6.bag",
    "run_hangar_0.825.bag",
    "run_overtakemap_0.6.bag",
    "run_overtakemap_0.825.bag",
]

# Lookahead steps (number of waypoints ahead)
LA_STEPS = [5, 10, 20, 30]

OUTPUT_CSV = "/home/sanjeev/f110_ws/src/Data/data_files/method2V3_data.csv"


# =============================================================
# HELPER — match nearest timestamp in array
# =============================================================
def nearest_by_time(data, t):
    idx = np.argmin(np.abs(data[:, 0] - t))
    return data[idx]


# =============================================================
# PROCESS ONE BAG FILE
# =============================================================
def process_bag(bag_path):

    print(f"\n  Processing: {os.path.basename(bag_path)}")

    bag = rosbag.Bag(bag_path)

    waypoints    = []
    odom_data    = []
    pose_data    = []
    control_data = []

    for topic, msg, t in bag.read_messages():

        if topic == "/global_waypoints":
            if not waypoints:                          # read once
                for wp in msg.wpnts:
                    waypoints.append([
                        wp.x_m,
                        wp.y_m,
                        wp.psi_rad,
                        wp.kappa_radpm,
                        wp.vx_mps
                    ])

        elif topic == "/car_state/odom":
            odom_data.append([
                t.to_sec(),
                msg.pose.pose.position.x,
                msg.pose.pose.position.y,
                msg.twist.twist.linear.x,   # vx  — forward velocity
                msg.twist.twist.linear.y    # vy  — lateral velocity (slip proxy)
            ])

        elif topic == "/car_state/pose":
            quat = msg.pose.orientation
            yaw  = euler_from_quaternion([
                quat.x, quat.y, quat.z, quat.w
            ])[2]
            pose_data.append([t.to_sec(), yaw])

        elif topic == "/vesc/high_level/ackermann_cmd_mux/input/nav_1":
            control_data.append([t.to_sec(), msg.drive.steering_angle])

    bag.close()

    if not waypoints or not odom_data or not pose_data or not control_data:
        print(f"  ⚠️  Skipping — missing topics in {os.path.basename(bag_path)}")
        return []

    waypoints    = np.array(waypoints)
    odom_data    = np.array(odom_data)
    pose_data    = np.array(pose_data)
    control_data = np.array(control_data)

    tree    = KDTree(waypoints[:, :2])
    n_wp    = len(waypoints)
    dataset = []

    for odom in odom_data:

        t, x, y, vx, vy = odom

        _, yaw      = nearest_by_time(pose_data, t)
        _, steering = nearest_by_time(control_data, t)

        dist, idx = tree.query([x, y])
        wp_x, wp_y, wp_yaw, kappa, wp_vx = waypoints[idx]

        # ===== d_m — signed lateral error =====
        dx    = x - wp_x
        dy    = y - wp_y
        d_m   = np.sqrt(dx**2 + dy**2)
        cross = np.cross(
            np.array([np.cos(wp_yaw), np.sin(wp_yaw)]),
            np.array([dx, dy])
        )
        d_m = np.sign(cross) * d_m

        # ===== heading error =====
        heading_error = np.arctan2(
            np.sin(yaw - wp_yaw),
            np.cos(yaw - wp_yaw)
        )

        # ===== four lookahead curvatures =====
        kappas_la = []
        for steps in LA_STEPS:
            idx_la = min(idx + steps, n_wp - 1)
            kappas_la.append(waypoints[idx_la][3])

        dataset.append([
            d_m,
            heading_error,
            kappa,
            vx,
            kappas_la[0],   # kappa_la_5
            kappas_la[1],   # kappa_la_10
            kappas_la[2],   # kappa_la_20
            kappas_la[3],   # kappa_la_30
            vy,
            steering
        ])

    print(f"  ✅ Extracted {len(dataset)} samples")
    return dataset


# =============================================================
# MAIN
# =============================================================
all_samples = []

for bag_name in TRAINING_BAGS:
    bag_path = os.path.join(BAG_DIR, bag_name)
    if not os.path.exists(bag_path):
        print(f"  ⚠️  Not found, skipping: {bag_name}")
        continue
    samples = process_bag(bag_path)
    all_samples.extend(samples)

print(f"\n✅ Total raw samples from all bags: {len(all_samples)}")

# =============================================================
# DATA AUGMENTATION — mirror every sample left ↔ right
# Flips the sign of: d_m, heading_error, all kappas, vy, steering
# vx stays the same (speed doesn't change direction)
# Doubles the dataset and balances left/right turns
# =============================================================
cols = [
    "d_m", "heading_error", "kappa", "vx",
    "kappa_la_5", "kappa_la_10", "kappa_la_20", "kappa_la_30",
    "vy", "steering"
]

df_raw = pd.DataFrame(all_samples, columns=cols)

df_mirror = df_raw.copy()
df_mirror["d_m"]           = -df_raw["d_m"]
df_mirror["heading_error"] = -df_raw["heading_error"]
df_mirror["kappa"]         = -df_raw["kappa"]
df_mirror["kappa_la_5"]    = -df_raw["kappa_la_5"]
df_mirror["kappa_la_10"]   = -df_raw["kappa_la_10"]
df_mirror["kappa_la_20"]   = -df_raw["kappa_la_20"]
df_mirror["kappa_la_30"]   = -df_raw["kappa_la_30"]
df_mirror["vy"]            = -df_raw["vy"]
df_mirror["steering"]      = -df_raw["steering"]

df_final = pd.concat([df_raw, df_mirror], ignore_index=True)

# =============================================================
# SAVE
# =============================================================
df_final.to_csv(OUTPUT_CSV, index=False)

print(f"✅ After mirroring augmentation: {len(df_final)} samples")
print(f"✅ Saved to: {OUTPUT_CSV}")
print(f"\nColumns: {list(df_final.columns)}")
print(df_final.describe())
