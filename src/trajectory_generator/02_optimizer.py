import numpy as np
from scipy.signal import savgol_filter

def minimize_curvature(x,y):

    window = 31
    poly = 3

    x_s = savgol_filter(x,window,poly)
    y_s = savgol_filter(y,window,poly)

    return x_s,y_s