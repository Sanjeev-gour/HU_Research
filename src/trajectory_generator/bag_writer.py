#!/usr/bin/env python3

import rosbag
import rospy
import numpy as np

from f110_msgs.msg import Wpnt
from f110_msgs.msg import WpntArray

def save_waypoints_bag(filename, x, y, v, kappa):

    rospy.init_node("trajectory_bag_writer", anonymous=True)

    bag = rosbag.Bag(filename, 'w')

    wp_array = WpntArray()
    wp_array.wpnts = []

    ds = np.sqrt(np.diff(x)**2 + np.diff(y)**2)
    s_list = np.insert(np.cumsum(ds), 0, 0.0)

    for i in range(len(x)):
        wp = Wpnt()

        wp.id = i
        wp.s_m = float(s_list[i])
        wp.d_m = 0.0
        wp.x_m = float(x[i])
        wp.y_m = float(y[i])
        wp.d_right = 1.0
        wp.d_left = 1.0

        # compute heading properly
        if i < len(x) - 1:
            dx = x[i+1] - x[i]
            dy = y[i+1] - y[i]
            wp.psi_rad = float(np.arctan2(dy, dx))
        else:
            wp.psi_rad = 0.0

        wp.kappa_radpm = float(kappa[i])
        wp.vx_mps = float(v[i])
        wp.ax_mps2 = 0.0

        wp_array.wpnts.append(wp)

    # 🔥 WRITE MULTIPLE TIMES (CRITICAL FIX)
    for t in np.linspace(0, 2.0, 20):
        bag.write("/global_waypoints", wp_array, rospy.Time.from_sec(t))

    bag.close()

    print("Saved:", filename)