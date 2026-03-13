import numpy as np

def compute_velocity_profile(kappa, mu=1.0, g=9.81,
                             max_speed=8.0,
                             accel_limit=2.0,
                             ds=0.05):

    # Lateral friction limit
    v_max_curve = np.sqrt(np.clip(mu * g / (np.abs(kappa) + 1e-6), 0, max_speed**2))
    v = np.minimum(v_max_curve, max_speed)

    # Forward pass (acceleration constraint)
    for i in range(1, len(v)):
        v[i] = min(v[i],
                   np.sqrt(v[i-1]**2 + 2 * accel_limit * ds))

    # Backward pass (braking constraint)
    for i in range(len(v)-2, -1, -1):
        v[i] = min(v[i],
                   np.sqrt(v[i+1]**2 + 2 * accel_limit * ds))

    return v