#!/usr/bin/env python3

import rosbag
import csv

bag = rosbag.Bag("lap_record.bag")

x_list = []
y_list = []

for topic, msg, t in bag.read_messages():
    # Print topic once to debug
    print("Reading topic:", topic)
    break

# Now actually extract
for topic, msg, t in bag.read_messages():
    if "odom" in topic:
        x = msg.pose.pose.position.x
        y = msg.pose.pose.position.y
        x_list.append(x)
        y_list.append(y)

bag.close()

print("Total points extracted:", len(x_list))

with open("centerline.csv", "w") as f:
    writer = csv.writer(f)
    for x, y in zip(x_list, y_list):
        writer.writerow([x, y])

print("centerline.csv generated.")