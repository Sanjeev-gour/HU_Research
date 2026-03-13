#!/usr/bin/env python3

import numpy as np

from geometry import compute_spline
from curvature import compute_curvature
from optimizer import minimize_curvature
from velocity import compute_velocity_profile
from bag_writer import save_waypoints_bag

# --------------------------------------------------
# Load centerline
# --------------------------------------------------
# centerline.csv must contain:
# x,y
centerline = np.loadtxt("centerline.csv", delimiter=',')

x = centerline[:, 0]
y = centerline[:, 1]

# --------------------------------------------------
# Optimize (minimize curvature approx)
# --------------------------------------------------
x_opt, y_opt = minimize_curvature(x, y)

# --------------------------------------------------
# Generate smooth spline
# --------------------------------------------------
x_spline, y_spline, tck = compute_spline(x_opt, y_opt)

# --------------------------------------------------
# Compute curvature
# --------------------------------------------------
kappa = compute_curvature(tck)

# --------------------------------------------------
# Compute velocity profile
# --------------------------------------------------
velocity = compute_velocity_profile(kappa)

# --------------------------------------------------
# Save bag file
# --------------------------------------------------
save_waypoints_bag("global_wpnts.bag",
                   x_spline,
                   y_spline,
                   velocity,
                   kappa)

print("Trajectory generation complete.")