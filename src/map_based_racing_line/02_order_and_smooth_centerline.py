import numpy as np
import csv
from scipy.interpolate import splprep, splev
from scipy.spatial import KDTree

print("Loading raw centerline...")

data = np.loadtxt("centerline_raw.csv", delimiter=",", skiprows=1)

points = data[:,0:2]

print("Ordering centerline using KDTree...")

tree = KDTree(points)

ordered = [points[0]]
visited = set([0])

for i in range(len(points)-1):

    dist, idx = tree.query(ordered[-1], k=10)

    for j in idx:
        if j not in visited:
            ordered.append(points[j])
            visited.add(j)
            break

ordered = np.array(ordered)

x = ordered[:,0]
y = ordered[:,1]

print("Fitting spline and resampling trajectory...")

tck, u = splprep([x,y], s=5)

u_new = np.linspace(0,1,2000)

x_new, y_new = splev(u_new, tck)

window = 35

x_smooth = np.convolve(x_new, np.ones(window)/window, mode='same')
y_smooth = np.convolve(y_new, np.ones(window)/window, mode='same')

print("Saving centerline_smooth.csv")

with open("centerline_smooth.csv","w") as f:

    writer = csv.writer(f)
    writer.writerow(["x","y"])

    for i in range(len(x_smooth)):
        writer.writerow([x_smooth[i], y_smooth[i]])

print("Centerline smoothing complete")