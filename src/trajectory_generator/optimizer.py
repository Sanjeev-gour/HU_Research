import numpy as np
from scipy.signal import savgol_filter

def minimize_curvature(x, y):
    """
    Approximate minimum curvature by smoothing path.
    """
    x_smooth = savgol_filter(x, 51, 3)
    y_smooth = savgol_filter(y, 51, 3)

    return x_smooth, y_smooth