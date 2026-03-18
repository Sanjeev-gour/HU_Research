import rosbag
import csv

bag = rosbag.Bag('global_wpnts.bag')

with open('global_wpnts.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerow(['x', 'y', 'speed'])

    for topic, msg, t in bag.read_messages(topics=['/global_waypoints']):
        
        for wp in msg.wpnts:
            x = wp.x_m
            y = wp.y_m
            speed = wp.vx_mps  # speed

            writer.writerow([x, y, speed])

bag.close()

print("Extraction complete ✅")