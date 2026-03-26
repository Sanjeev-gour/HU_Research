import rosbag
import csv

bag = rosbag.Bag('global_wpnts.bag')

with open('global_wpnts_overtake_xy.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerow(['x', 'y'])   # only x, y

    for topic, msg, t in bag.read_messages(topics=['/global_waypoints']):
        
        for wp in msg.wpnts:
            x = wp.x_m
            y = wp.y_m

            writer.writerow([x, y])

bag.close()

print("Extraction complete ✅")