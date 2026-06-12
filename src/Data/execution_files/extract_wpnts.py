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


# code to check the fields of the global_wpnts.bag
# import rosbag

# bag = rosbag.Bag('global_wpnts.bag')

# for topic, msg, t in bag.read_messages(topics=['/global_waypoints']):
    
#     print("📦 Message type:", type(msg))
#     print("\n🔹 Top-level fields in message:")
#     print(msg.__slots__)   # fields of the message

#     # check waypoint fields
#     if hasattr(msg, 'wpnts') and len(msg.wpnts) > 0:
#         wp = msg.wpnts[0]

#         print("\n🚗 Waypoint fields:")
#         print(wp.__slots__)   # fields inside each waypoint

#     break   # only need first message

# bag.close()