import numpy as np

def compute_velocity_profile(kappa,
                             mu=1.0,
                             g=9.81,
                             max_speed=8.0,
                             accel_limit=3.0,
                             ds=0.05):

    kappa = np.abs(kappa)

    # Avoid division explosion
    kappa = np.clip(kappa, 0.001, None)

    v_max_curve = np.sqrt(mu * g / kappa)

    v = np.minimum(v_max_curve, max_speed)

    # forward pass
    for i in range(1, len(v)):
        v[i] = min(v[i], np.sqrt(v[i-1]**2 + 2*accel_limit*ds))

    # backward pass
    for i in range(len(v)-2, -1, -1):
        v[i] = min(v[i], np.sqrt(v[i+1]**2 + 2*accel_limit*ds))

    # guarantee minimum movement
    v = np.clip(v, 1.5, max_speed)

    return v