import numpy as np
import csv

print("Loading smoothed centerline...")

data = np.loadtxt("centerline_smooth.csv", delimiter=",", skiprows=1)

x = data[:,0]
y = data[:,1]

dx = np.gradient(x)
dy = np.gradient(y)

ddx = np.gradient(dx)
ddy = np.gradient(dy)

kappa = (dx*ddy - dy*ddx) / ((dx**2 + dy**2)**1.5 + 1e-6)

kappa = np.abs(kappa)

mu = 0.9
g = 9.81
max_speed = 2.5

v = np.sqrt((mu*g)/(kappa + 1e-6))

v = np.clip(v, 1.0, max_speed)

# Smooth velocity
window = 25
v = np.convolve(v, np.ones(window)/window, mode='same')

print("Velocity range:", np.min(v), np.max(v))

with open("map_based_trajectory.csv","w") as f:
    writer = csv.writer(f)
    writer.writerow(["x","y","velocity","curvature"])

    for i in range(len(x)):
        writer.writerow([x[i], y[i], v[i], kappa[i]])

print("map_based_trajectory.csv generated")