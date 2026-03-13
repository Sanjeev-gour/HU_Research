#!/usr/bin/env python3

import numpy as np
import rosbag
import rospy
from f110_msgs.msg import Wpnt
from f110_msgs.msg import WpntArray

print("Loading map_based_trajectory.csv")

data = np.loadtxt("optimized_trajectory.csv", delimiter=",", skiprows=1)

x = data[:,0]
y = data[:,1]
v = data[:,2]
kappa = data[:,3]

# Map parameters (from YAML file)
resolution = 0.05
origin_x = -10.0
origin_y = -10.0

# Compute heading
dx = np.gradient(x)
dy = np.gradient(y)

psi = np.arctan2(dy, dx)

# Compute arc length
ds = np.sqrt(np.diff(x)**2 + np.diff(y)**2)
s = np.insert(np.cumsum(ds), 0, 0)

rospy.init_node("map_based_waypoint_writer")

bag = rosbag.Bag("global_wpnts.bag", "w")

wp_array = WpntArray()

print("Generating waypoint array...")

for i in range(len(x)):

    wp = Wpnt()

    wp.id = i

    wp.s_m = float(s[i])
    wp.d_m = 0.0

    # Convert pixels to world coordinates
    wp.x_m = float(x[i] * resolution + origin_x)
    wp.y_m = float(y[i] * resolution + origin_y)

    wp.psi_rad = float(psi[i])

    wp.kappa_radpm = float(kappa[i])

    wp.vx_mps = float(v[i])
    wp.ax_mps2 = 0.0

    wp.d_left = 1.5
    wp.d_right = 1.5

    wp_array.wpnts.append(wp)

print("Writing bag file...")

for i in range(20):

    t = rospy.Time(i)

    bag.write("/global_waypoints", wp_array, t)

bag.close()

print("global_wpnts.bag generated successfully")