import numpy as np
import csv
from scipy.ndimage import gaussian_filter1d

print("Loading trajectory...")

data = np.loadtxt("map_based_trajectory.csv", delimiter=",", skiprows=1)

x = data[:,0]
y = data[:,1]
v = data[:,2]
kappa = data[:,3]

print("Computing racing line shift...")

dx = np.gradient(x)
dy = np.gradient(y)

norm = np.sqrt(dx**2 + dy**2)

nx = -dy / norm
ny = dx / norm

# shift trajectory opposite to curvature
shift = -0.3 * np.sign(np.gradient(kappa))

x_race = x + shift * nx
y_race = y + shift * ny

# smooth racing line
x_race = gaussian_filter1d(x_race, 15)
y_race = gaussian_filter1d(y_race, 15)

print("Saving optimized trajectory")

with open("optimized_trajectory.csv","w") as f:

    writer = csv.writer(f)

    writer.writerow(["x","y","velocity","curvature"])

    for i in range(len(x_race)):
        writer.writerow([x_race[i], y_race[i], v[i], kappa[i]])

print("optimized_trajectory.csv generated")