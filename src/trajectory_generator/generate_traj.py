#!/usr/bin/env python3

import numpy as np

from geometry import compute_spline
from curvature import compute_curvature
from optimizer import minimize_curvature
from velocity import compute_velocity_profile
from bag_writer import save_waypoints_bag

def resample(x,y,ds=0.05):

    dist = np.sqrt(np.diff(x)**2 + np.diff(y)**2)
    s = np.insert(np.cumsum(dist),0,0)

    s_new = np.arange(0,s[-1],ds)

    x_new = np.interp(s_new,s,x)
    y_new = np.interp(s_new,s,y)

    return x_new,y_new

centerline = np.loadtxt("centerline.csv",delimiter=',')

x = centerline[:,0]
y = centerline[:,1]

# important step
x,y = resample(x,y)

x_opt,y_opt = minimize_curvature(x,y)

x_spline,y_spline,tck = compute_spline(x_opt,y_opt)

kappa = compute_curvature(tck,len(x_spline))

velocity = compute_velocity_profile(kappa)

save_waypoints_bag(
    "global_wpnts.bag",
    x_spline,
    y_spline,
    velocity,
    kappa
)

print("Trajectory generation complete.")