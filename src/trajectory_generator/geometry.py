import numpy as np
from scipy.interpolate import splprep, splev

def compute_spline(x, y, num_points=1000):
    """
    Fit periodic spline to closed track.
    """
    tck, u = splprep([x, y], s=0, per=True)
    u_fine = np.linspace(0, 1, num_points)

    x_fine, y_fine = splev(u_fine, tck)
    return np.array(x_fine), np.array(y_fine), tck