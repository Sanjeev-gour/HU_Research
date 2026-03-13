import numpy as np
from scipy.interpolate import splev

def compute_curvature(tck, num_points=1000):
    """
    Compute curvature using parametric derivatives.
    """
    u_fine = np.linspace(0, 1, num_points)

    dx, dy = splev(u_fine, tck, der=1)
    ddx, ddy = splev(u_fine, tck, der=2)

    numerator = dx * ddy - dy * ddx
    denominator = (dx**2 + dy**2)**1.5 + 1e-6

    kappa = numerator / denominator
    return kappa