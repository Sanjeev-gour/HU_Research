#!/usr/bin/env python3

# =============================================================
# HOW TO USE THIS FILE
# =============================================================
# STEP 0 — Record a lap while the car is running:
#
#   Terminal 1: roslaunch map_controller sim_MAP.launch map_name:=overtake_map
#   Terminal 2: cd /home/sanjeev/f110_ws/src/trajectory_generator
#               rosbag record -O overtake_map_lap_record.bag /car_state/odom
#
#   Let the car complete one full lap, then press Ctrl+C to stop.
#
# STEP 1 — Run this file to extract x,y path from the bag:
#
#   python3 01_extract_path.py
#   Output: overtake_map_centerline_xy.csv
#
# STEP 2 — Run 07_generate_traj.py to generate the final trajectory bag:
#
#   python3 07_generate_traj.py
#   Output: global_wpnts.bag
#
# STEP 3 — Copy global_wpnts.bag to the map folder:
#
#   cp global_wpnts.bag /home/sanjeev/f110_ws/src/F110_ROS_Simulator/maps/overtake_map/
# =============================================================

import rosbag
import csv
import numpy as np

# open the recorded bag file
bag = rosbag.Bag("overtake_map_lap_record.bag")

# extract x, y positions from the odom topic
points = []

for topic, msg, t in bag.read_messages():
    if "odom" in topic:
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        points.append([x,y])

bag.close()

points = np.array(points)

# downsample: take every 4th point to remove controller oscillations
points = points[::4]

# save directly as the centerline CSV used by 07_generate_traj.py
with open("overtake_map_centerline_xy.csv","w") as f:
    writer = csv.writer(f)
    writer.writerows(points)

print("overtake_map_centerline_xy.csv generated")