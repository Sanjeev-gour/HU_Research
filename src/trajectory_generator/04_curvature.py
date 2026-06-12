import numpy as np
from scipy.interpolate import splev

def compute_curvature(tck,num_points=1000):

    u = np.linspace(0,1,num_points)

    dx,dy = splev(u,tck,der=1)
    ddx,ddy = splev(u,tck,der=2)

    kappa = (dx*ddy - dy*ddx)/((dx**2 + dy**2)**1.5 + 1e-6)

    return kappa