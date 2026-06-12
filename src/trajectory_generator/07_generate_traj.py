#!/usr/bin/env python3

import numpy as np

import importlib
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

_opt = importlib.import_module('02_optimizer')
_geo = importlib.import_module('03_geometry')
_cur = importlib.import_module('04_curvature')
_vel = importlib.import_module('05_velocity')
_bag = importlib.import_module('06_bag_writer')

minimize_curvature       = _opt.minimize_curvature
compute_spline           = _geo.compute_spline
compute_curvature        = _cur.compute_curvature
compute_velocity_profile = _vel.compute_velocity_profile
save_waypoints_bag       = _bag.save_waypoints_bag

def resample(x,y,ds=0.05):

    dist = np.sqrt(np.diff(x)**2 + np.diff(y)**2)

    s = np.insert(np.cumsum(dist),0,0)

    s_new = np.arange(0,s[-1],ds)

    x_new = np.interp(s_new,s,x)
    y_new = np.interp(s_new,s,y)

    return x_new,y_new

centerline = np.loadtxt("overtake_map_centerline_xy.csv",delimiter=',')

x = centerline[:,0]
y = centerline[:,1]

# uniform spacing
x,y = resample(x,y)

# smoothing
x_opt,y_opt = minimize_curvature(x,y)

# spline
x_spline,y_spline,tck = compute_spline(x_opt,y_opt)

# curvature
kappa = compute_curvature(tck,len(x_spline))

# compute real ds
ds = np.mean(np.sqrt(np.diff(x_spline)**2 + np.diff(y_spline)**2))

# velocity
velocity = compute_velocity_profile(kappa,ds=ds)

# save bag
save_waypoints_bag(
    "global_wpnts.bag",
    x_spline,
    y_spline,
    velocity,
    kappa
)

print("Trajectory generation complete.")