#!/usr/bin/env python3
"""
plot_trajectories.py — generates two paper figures:

    fig4_maps.png          racetrack layout overview (all 5 maps)
    fig10_trajectories.png MAP vs NN trajectory comparison (all 5 maps)

Requires in bag_files/:
    run_<map>_0.825.bag    MAP controller closed-loop run
    nn_<map>_0.825.bag     NN  controller closed-loop run

Usage:
    source /opt/ros/noetic/setup.bash
    python3 plot_trajectories.py
"""

import os
import numpy as np
import yaml
import rosbag
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from PIL import Image

BAG_DIR = os.path.expanduser('~/f110_ws/src/Data/bag_files')
MAP_DIR = os.path.expanduser('~/f110_ws/src/F110_ROS_Simulator/maps')
OUT_DIR = os.path.expanduser('~/f110_ws/src/Data/plots&fig')
OUT_FIG4  = os.path.join(OUT_DIR, 'fig4_maps.png')
OUT_FIG10 = os.path.join(OUT_DIR, 'fig10_trajectories.png')

MAP_C = '#1565C0'   # blue  — MAP controller
NN_C  = '#E65100'   # orange — NN controller
RL_C  = '#222222'   # dark  — racing line

SKIP = 80  # messages to drop at bag start (avoids launch transients)

MAPS = [
    dict(label='Overtake', map_dir='overtake_map', map_file='overtake_map',
         map_bag='run_overtakemap_0.825.bag', nn_bag='nn_overtake_map_0.825.bag',
         n_pts=None, one_lap=False),
    dict(label='Porto',    map_dir='porto',        map_file='porto',
         map_bag='run_porto_0.825.bag',       nn_bag='nn_porto_0.825.bag',
         n_pts=None, one_lap=False),
    dict(label='Hangar',   map_dir='hangar',       map_file='hangar',
         map_bag='run_hangar_0.825.bag',      nn_bag='nn_hangar_0.825.bag',
         n_pts=None, one_lap=False),
    dict(label='Berlin',   map_dir='berlin',       map_file='berlin',
         map_bag='run_berlin_0.825.bag',      nn_bag='nn_berlin_0.825.bag',
         n_pts=None, one_lap=True),
    dict(label='F Map',    map_dir='f',            map_file='f',
         map_bag='run_f_0.825.bag',           nn_bag='nn_f_0.825.bag',
         n_pts=None, one_lap=True),
]


def read_poses(bag_path, n_max=None, one_lap=False):
    """Extract (x, y) from /car_state/pose.

    one_lap=True stops when the car returns within 1.5 m of its start position
    (after at least 200 points), giving one clean closed lap for tracks where
    the bag contains multiple laps.
    """
    xs, ys = [], []
    with rosbag.Bag(bag_path) as bag:
        for i, (_, msg, _) in enumerate(bag.read_messages('/car_state/pose')):
            if i < SKIP:
                continue
            if n_max and len(xs) >= n_max:
                break
            xs.append(msg.pose.position.x)
            ys.append(msg.pose.position.y)
            if one_lap and len(xs) > 200:
                if np.hypot(xs[-1] - xs[0], ys[-1] - ys[0]) < 1.5:
                    break
    return np.array(xs), np.array(ys)


def read_racing_line(bag_path):
    """Extract the precomputed racing line from /global_waypoints."""
    with rosbag.Bag(bag_path) as bag:
        for _, msg, _ in bag.read_messages('/global_waypoints'):
            return np.array([w.x_m for w in msg.wpnts]), \
                   np.array([w.y_m for w in msg.wpnts])
    return np.array([]), np.array([])


def world_to_pixel(wx, wy, origin_x, origin_y, resolution, img_h):
    px = (wx - origin_x) / resolution
    py = img_h - (wy - origin_y) / resolution
    return px, py


def crop_bounds(img, pad=20):
    """Return pixel crop bounds tightly around the white track area."""
    mask = img > 50  # white pixels = drivable track
    rows = np.where(np.any(mask, axis=1))[0]
    cols = np.where(np.any(mask, axis=0))[0]
    h, w = img.shape
    r0 = max(0,   rows[0]  - pad)
    r1 = min(h-1, rows[-1] + pad)
    c0 = max(0,   cols[0]  - pad)
    c1 = min(w-1, cols[-1] + pad)
    return r0, r1, c0, c1


def plot_maps():
    """Fig 4 — racetrack layout overview."""
    fig, axes = plt.subplots(1, 5, figsize=(18, 4.5), facecolor='white')
    fig.suptitle('Racetracks Used in This Study', fontsize=14, fontweight='bold', y=1.01)

    for ax, cfg in zip(axes, MAPS):
        img_path = os.path.join(MAP_DIR, cfg['map_dir'], cfg['map_file'] + '.png')
        img = np.array(Image.open(img_path).convert('L'))
        r0, r1, c0, c1 = crop_bounds(img)
        ax.imshow(img[r0:r1, c0:c1], cmap='gray_r', origin='upper', aspect='equal')
        ax.set_title(cfg['label'], fontsize=12, fontweight='bold', pad=6)
        ax.axis('off')

    plt.tight_layout(pad=0.5)
    os.makedirs(OUT_DIR, exist_ok=True)
    plt.savefig(OUT_FIG4, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Saved -> {OUT_FIG4}")


def plot_trajectories():
    """Fig 10 — MAP vs NN trajectory comparison overlaid on track maps."""
    fig, axes = plt.subplots(1, 5, figsize=(18, 5.5), facecolor='white')

    for ax, cfg in zip(axes, MAPS):
        print(f"  {cfg['label']} ...", flush=True)

        img_path  = os.path.join(MAP_DIR, cfg['map_dir'], cfg['map_file'] + '.png')
        yaml_path = os.path.join(MAP_DIR, cfg['map_dir'], cfg['map_file'] + '.yaml')
        map_bag   = os.path.join(BAG_DIR, cfg['map_bag'])
        nn_bag    = os.path.join(BAG_DIR, cfg['nn_bag'])

        img = 255 - np.array(Image.open(img_path).convert('L'))  # invert: dark walls on white
        img_h, img_w = img.shape

        with open(yaml_path) as f:
            ym = yaml.safe_load(f)
        ox, oy, res = ym['origin'][0], ym['origin'][1], ym['resolution']

        def w2p(wx, wy):
            return world_to_pixel(wx, wy, ox, oy, res, img_h)

        rl_x,  rl_y  = read_racing_line(map_bag)
        map_x, map_y = read_poses(map_bag, n_max=cfg['n_pts'], one_lap=cfg['one_lap'])
        nn_x,  nn_y  = read_poses(nn_bag,  n_max=cfg['n_pts'], one_lap=cfg['one_lap'])

        rl_px,  rl_py  = w2p(rl_x,  rl_y)
        map_px, map_py = w2p(map_x, map_y)
        nn_px,  nn_py  = w2p(nn_x,  nn_y)

        # crop tightly around the track using dark pixels (walls after inversion)
        mask = img < 240
        rows = np.where(np.any(mask, axis=1))[0]
        cols = np.where(np.any(mask, axis=0))[0]
        pad = 20
        r0 = max(0,       rows[0]  - pad);  r1 = min(img_h-1, rows[-1] + pad)
        c0 = max(0,       cols[0]  - pad);  c1 = min(img_w-1, cols[-1] + pad)

        ax.imshow(img[r0:r1, c0:c1], cmap='gray', vmin=0, vmax=255,
                  origin='upper', aspect='equal', alpha=0.35)
        ax.plot(rl_px  - c0, rl_py  - r0, '-', color=RL_C,  lw=1.2, alpha=0.7,  zorder=2)
        ax.plot(map_px - c0, map_py - r0, '-', color=MAP_C, lw=1.8, alpha=0.85, zorder=3)
        ax.plot(nn_px  - c0, nn_py  - r0, '-', color=NN_C,  lw=1.8, alpha=0.85, zorder=4)

        ax.set_xlim(0, c1 - c0)
        ax.set_ylim(r1 - r0, 0)
        ax.set_aspect('equal')
        ax.axis('off')
        ax.set_title(cfg['label'], fontsize=12, fontweight='bold', pad=6)

    handles = [
        mpatches.Patch(color=RL_C,  label='Racing line (reference)'),
        plt.Line2D([0], [0], color=MAP_C, lw=2.5, label='MAP controller'),
        plt.Line2D([0], [0], color=NN_C,  lw=2.5, label='Our Method (NN)'),
    ]
    fig.legend(handles=handles, loc='lower center', ncol=3, fontsize=11,
               frameon=True, bbox_to_anchor=(0.5, -0.02), framealpha=0.95, edgecolor='#cccccc')
    fig.suptitle('Trajectories at Velocity Scale 0.825 — All Five Racetracks',
                 fontsize=14, fontweight='bold', y=1.02)

    plt.tight_layout(pad=0.8, w_pad=0.8)
    plt.savefig(OUT_FIG10, dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    print(f"Saved -> {OUT_FIG10}")


if __name__ == '__main__':
    plot_maps()
    plot_trajectories()
