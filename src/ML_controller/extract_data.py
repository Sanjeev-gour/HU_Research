# import rosbag
# import csv
# from tf.transformations import euler_from_quaternion

# bag = rosbag.Bag("lap_data_1.bag")

# data = []

# pose = None
# speed = None

# for topic, msg, t in bag.read_messages():

#     if topic == "/car_state/pose":

#         x = msg.pose.position.x
#         y = msg.pose.position.y

#         q = msg.pose.orientation
#         yaw = euler_from_quaternion([q.x,q.y,q.z,q.w])[2]

#         pose = [x,y,yaw]

#     if topic == "/vesc/high_level/ackermann_cmd_mux/input/nav_1":

#         steering = msg.drive.steering_angle
#         speed = msg.drive.speed

#         if pose is not None:
#             data.append(pose + [steering,speed])

# bag.close()

# with open("training_data_1.csv","w") as f:
#     writer = csv.writer(f)
#     writer.writerow(["x","y","yaw","steering","speed"])
#     writer.writerows(data)

# print("CSV generated")

#!/usr/bin/env python3

import rosbag
import csv
import numpy as np
from tf.transformations import euler_from_quaternion

bag = rosbag.Bag("lap_data_1.bag")

data = []

pose = None

# ============================
# STEP 1: EXTRACT RAW DATA
# ============================

for topic, msg, t in bag.read_messages():

    if topic == "/car_state/pose":

        x = msg.pose.position.x
        y = msg.pose.position.y

        q = msg.pose.orientation
        yaw = euler_from_quaternion([q.x, q.y, q.z, q.w])[2]

        pose = [x, y, yaw]

    if topic == "/vesc/high_level/ackermann_cmd_mux/input/nav_1":

        steering = msg.drive.steering_angle
        speed = msg.drive.speed

        if pose is not None:
            data.append(pose + [steering, speed])

bag.close()

data = np.array(data)

x = data[:, 0]
y = data[:, 1]
yaw = data[:, 2]
steering = data[:, 3]
speed = data[:, 4]

# ============================
# STEP 2: COMPUTE CURVATURE
# ============================

dx = np.gradient(x)
dy = np.gradient(y)

ddx = np.gradient(dx)
ddy = np.gradient(dy)

kappa = (dx * ddy - dy * ddx) / (dx**2 + dy**2 + 1e-6)**1.5

# ============================
# STEP 3: BUILD FINAL DATASET
# ============================

dataset = []

window = 2  # for context (i-2 to i+2)

for i in range(window, len(kappa) - window):

    # curvature window (VERY IMPORTANT)
    kappa_window = kappa[i-2:i+3]

    row = list(kappa_window) + [
        yaw[i],
        steering[i],
        speed[i]
    ]

    dataset.append(row)

# ============================
# STEP 4: SAVE CSV
# ============================

header = [
    "kappa_m2", "kappa_m1", "kappa_0", "kappa_p1", "kappa_p2",
    "yaw",
    "steering",
    "speed"
]

with open("training_data_final.csv", "w") as f:
    writer = csv.writer(f)
    writer.writerow(header)
    writer.writerows(dataset)

print("✅ Final ML dataset generated")