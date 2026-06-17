#!/usr/bin/env python3
"""
extract_data_method2.py  —  Method 2 Full Data Pipeline

For each map, reads the 0.6 and 0.825 rosbags, extracts the 5
physics-informed features + steering label, applies the 8-step
cleaning pipeline, and saves the leave-one-map-out training split:

    method2V1V2_traintest_<map>.csv  (other 4 maps, both speeds, cleaned)

Usage:
    # Process all maps (full pipeline):
    python3 extract_data_method2.py

    # Process a single map only:
    python3 extract_data_method2.py --map porto
"""

import argparse
import os
import numpy as np
import pandas as pd
from scipy.spatial import KDTree

BAG_DIR  = "/home/sanjeev/f110_ws/src/Data/bag_files"
DATA_DIR = "/home/sanjeev/f110_ws/src/Data/data_files"

MAPS      = ["overtake_map", "berlin", "hangar", "f", "porto"]
SPEEDS    = ["0.6", "0.825"]
LOOKAHEAD   = 10
RANDOM_SEED = 42

# Bag filenames don't always match the map name exactly
BAG_PREFIX = {
    "overtake_map": "overtakemap",  # actual files: run_overtakemap_*.bag
}


# =============================================================================
# STEP 1: EXTRACT  —  rosbag → raw feature rows
# =============================================================================
def extract_bag(map_name, speed):
    """Extract features from one bag. Returns a DataFrame, or None if missing."""
    import rosbag
    from tf.transformations import euler_from_quaternion

    bag_stem = BAG_PREFIX.get(map_name, map_name)
    bag_path = os.path.join(BAG_DIR, f"run_{bag_stem}_{speed}.bag")
    if not os.path.exists(bag_path):
        print(f"    !! missing bag, skipped: run_{bag_stem}_{speed}.bag")
        return None

    print(f"    extracting run_{bag_stem}_{speed}.bag ...", flush=True)
    bag = rosbag.Bag(bag_path)

    waypoints, odom_data, pose_data, control_data = [], [], [], []

    for topic, msg, t in bag.read_messages():
        if topic == "/global_waypoints":
            for wp in msg.wpnts:
                waypoints.append([wp.x_m, wp.y_m, wp.psi_rad,
                                   wp.kappa_radpm, wp.vx_mps])
        elif topic == "/car_state/odom":
            odom_data.append([t.to_sec(),
                               msg.pose.pose.position.x,
                               msg.pose.pose.position.y,
                               msg.twist.twist.linear.x])
        elif topic == "/car_state/pose":
            q = msg.pose.orientation
            yaw = euler_from_quaternion([q.x, q.y, q.z, q.w])[2]
            pose_data.append([t.to_sec(), yaw])
        elif topic == "/vesc/high_level/ackermann_cmd_mux/input/nav_1":
            control_data.append([t.to_sec(), msg.drive.steering_angle])

    bag.close()

    waypoints    = np.array(waypoints)
    odom_data    = np.array(odom_data)
    pose_data    = np.array(pose_data)
    control_data = np.array(control_data)

    tree = KDTree(waypoints[:, :2])

    def nearest(data, t):
        return data[np.argmin(np.abs(data[:, 0] - t))]

    rows = []
    for odom in odom_data:
        t, x, y, vx = odom
        _, yaw      = nearest(pose_data, t)
        _, steering = nearest(control_data, t)

        _, idx = tree.query([x, y])
        wp_x, wp_y, wp_yaw, kappa, _ = waypoints[idx]

        dx, dy  = x - wp_x, y - wp_y
        d_m     = np.sign(np.cross([np.cos(wp_yaw), np.sin(wp_yaw)],
                                   [dx, dy])) * np.hypot(dx, dy)
        heading_error = np.arctan2(np.sin(yaw - wp_yaw), np.cos(yaw - wp_yaw))
        kappa_la = waypoints[min(idx + LOOKAHEAD, len(waypoints) - 1), 3]

        rows.append([d_m, heading_error, kappa, vx, kappa_la, steering])

    df = pd.DataFrame(rows, columns=[
        "d_m", "heading_error", "kappa", "vx", "kappa_lookahead", "steering"
    ])
    print(f"      {len(df)} rows extracted")
    return df


# =============================================================================
# STEP 2: CLEAN  —  8-step pipeline (as reported in paper)
# =============================================================================
def clean(df):
    n0 = len(df)
    df = df.dropna()
    df = df[df["vx"] > 0.5]
    df = df[df["kappa"].abs() < 0.99]
    df = df[df["kappa_lookahead"].abs() < 0.99]
    df = df[df["d_m"].abs() < 0.5]
    Q1, Q3 = df["heading_error"].quantile([0.25, 0.75])
    IQR    = Q3 - Q1
    df = df[(df["heading_error"] >= Q1 - 1.5*IQR) &
            (df["heading_error"] <= Q3 + 1.5*IQR)]
    df = df[df["steering"].abs() < 0.39]
    df = df[df["vx"] <= 8.0]
    df = df.drop_duplicates().reset_index(drop=True)
    print(f"    cleaned: {n0} -> {len(df)} rows")
    return df


# =============================================================================
# STEP 3: BUILD SPLITS  —  leave-one-map-out training CSV per map
# =============================================================================
def build_split(test_map, all_maps):
    """Extract, merge, clean, and save training data for one holdout map."""
    train_maps = [m for m in all_maps if m != test_map]
    short      = test_map.replace("_map", "")   # overtake_map -> overtake

    print(f"\n{'='*55}")
    print(f"  Held-out: {test_map}")
    print(f"  Training: {train_maps}")
    print(f"{'='*55}")

    frames = []
    for m in train_maps:
        for s in SPEEDS:
            df = extract_bag(m, s)
            if df is not None:
                frames.append(df)

    merged  = pd.concat(frames, ignore_index=True)
    merged  = merged.sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)
    cleaned = clean(merged)

    out = os.path.join(DATA_DIR, f"method2V1V2_traintest_{short}.csv")
    cleaned.to_csv(out, index=False)
    print(f"  Saved -> {out}  ({len(cleaned)} rows)")


# =============================================================================
# ENTRY POINT
# =============================================================================
def main():
    parser = argparse.ArgumentParser(description='Method 2 data pipeline')
    parser.add_argument('--map', default=None,
                        help='process one held-out map only (e.g. porto)')
    args = parser.parse_args()

    maps_to_run = [args.map] if args.map else MAPS

    for test_map in maps_to_run:
        build_split(test_map, MAPS)

    print("\nDone.")


if __name__ == '__main__':
    main()
