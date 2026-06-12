import rosbag
import csv
from tf.transformations import euler_from_quaternion

bag = rosbag.Bag("lap_data_1.bag")

data = []

pose = None
speed = None

for topic, msg, t in bag.read_messages():

    if topic == "/car_state/pose":

        x = msg.pose.position.x
        y = msg.pose.position.y

        q = msg.pose.orientation
        yaw = euler_from_quaternion([q.x,q.y,q.z,q.w])[2]

        pose = [x,y,yaw]

    if topic == "/vesc/high_level/ackermann_cmd_mux/input/nav_1":

        steering = msg.drive.steering_angle
        speed = msg.drive.speed

        if pose is not None:
            data.append(pose + [steering,speed])

bag.close()

with open("training_data_1.csv","w") as f:
    writer = csv.writer(f)
    writer.writerow(["x","y","yaw","steering","speed"])
    writer.writerows(data)

print("CSV generated")