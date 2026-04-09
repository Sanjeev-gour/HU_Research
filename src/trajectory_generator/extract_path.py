#!/usr/bin/env python3

import rosbag
import csv
import numpy as np

bag = rosbag.Bag("lap_record.bag")

points = []

for topic, msg, t in bag.read_messages():
    if "odom" in topic:
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        points.append([x,y])

bag.close()

points = np.array(points)

# remove controller oscillation
points = points[::4]

with open("path.csv","w") as f:
    writer = csv.writer(f)
    writer.writerows(points)

print("path.csv generated")