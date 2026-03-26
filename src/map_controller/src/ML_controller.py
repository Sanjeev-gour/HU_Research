#!/usr/bin/env python3

import rospy
import numpy as np
import torch
import torch.nn as nn
import time

from ackermann_msgs.msg import AckermannDriveStamped
from geometry_msgs.msg import PoseStamped
from tf.transformations import euler_from_quaternion


class Controller:

    def __init__(self):

        rospy.init_node('ml_controller', anonymous=True)

        self.loop_rate = 40
        self.position = None

        # ===== MODEL =====
        self.model = nn.Sequential(
            nn.Linear(3,64),
            nn.ReLU(),
            nn.Linear(64,64),
            nn.ReLU(),
            nn.Linear(64,2)
        )

        # ===== LOAD MODEL =====
        model_path = "/home/sanjeev/f110_ws/src/ML_controller/ml_model_4.pth"
        self.model.load_state_dict(torch.load(model_path))
        self.model.eval()

        rospy.loginfo("✅ ML model loaded successfully")

        # ===== INFERENCE TIME TRACKING =====
        self.times = []
        self.counter = 0

        # ===== PUBLISHER =====
        self.drive_pub = rospy.Publisher(
            "/vesc/high_level/ackermann_cmd_mux/input/nav_1",
            AckermannDriveStamped,
            queue_size=10
        )

        # ===== SUBSCRIBER =====
        rospy.Subscriber("/car_state/pose", PoseStamped, self.car_state_cb)

    def car_state_cb(self, data):

        x = data.pose.position.x
        y = data.pose.position.y

        yaw = euler_from_quaternion([
            data.pose.orientation.x,
            data.pose.orientation.y,
            data.pose.orientation.z,
            data.pose.orientation.w
        ])[2]

        self.position = [x, y, yaw]

    def control_loop(self):

        rate = rospy.Rate(self.loop_rate)

        while not rospy.is_shutdown():

            if self.position is None:
                rate.sleep()
                continue

            x, y, yaw = self.position

            # ===== INPUT =====
            state = torch.tensor([x, y, yaw], dtype=torch.float32)

            # ===== INFERENCE TIMING =====
            start_time = time.perf_counter()

            with torch.no_grad():
                output = self.model(state)

            end_time = time.perf_counter()
            inference_time = (end_time - start_time) * 1000  # ms

            # ===== STORE TIMES =====
            self.times.append(inference_time)
            self.counter += 1

            # ===== PRINT AVERAGE EVERY 100 STEPS =====
            if self.counter % 100 == 0:
                avg_time = np.mean(self.times)
                rospy.loginfo(f"Average Inference Time: {avg_time:.4f} ms")

            # ===== OUTPUT =====
            steering = output[0].item()
            speed = output[1].item()

            # ===== SAFETY LIMITS =====
            steering = np.clip(steering, -0.4, 0.4)
            speed = np.clip(speed, 0, 6)

            # ===== PUBLISH =====
            ack_msg = AckermannDriveStamped()
            ack_msg.header.stamp = rospy.Time.now()
            ack_msg.header.frame_id = "base_link"

            ack_msg.drive.steering_angle = steering
            ack_msg.drive.speed = speed

            self.drive_pub.publish(ack_msg)

            rate.sleep()


if __name__ == "__main__":

    controller = Controller()
    controller.control_loop()