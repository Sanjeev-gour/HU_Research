import cv2
import numpy as np
import csv
from skimage.morphology import skeletonize

print("Loading map...")

map_path = "/home/sanjeev/f110_ws/src/F110_ROS_Simulator/maps/test_2/test_2.png"

img = cv2.imread(map_path, cv2.IMREAD_GRAYSCALE)

if img is None:
    print("ERROR: Map not found")
    exit()

# Track area extraction
binary = img < 200

print("Extracting centerline using skeletonization...")

skeleton = skeletonize(binary)

ys, xs = np.where(skeleton)

points = np.vstack((xs, ys)).T

print("Centerline points:", len(points))

with open("centerline_raw.csv","w") as f:
    writer = csv.writer(f)
    writer.writerow(["x","y"])
    writer.writerows(points)

print("centerline_raw.csv generated")