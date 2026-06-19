#!/usr/bin/env python3
"""
plot_trajectories.py — generates two paper figures:

    fig4_maps.png          racetrack layout overview (all 5 maps)
    fig8_trajectories.png  MAP vs NN trajectory comparison (all 5 maps, two velocity profiles)

Requires in bag_files/:
    run_<map>_0.825.bag    MAP controller closed-loop run at 0.825
    nn_<map>_0.825.bag     NN  controller closed-loop run at 0.825
    map_<map>_0.92.bag     MAP controller closed-loop run at 0.92
    nn_<map>_0.92.bag      NN  controller closed-loop run at 0.92

All bags are recorded at 100 Hz on /car_state/pose.
Crashes produce stationary frames (dist ≈ 0), NOT position jumps.

Usage:
    source /opt/ros/noetic/setup.bash
    python3 plot_trajectories.py
"""

import os
import shutil
import numpy as np
import yaml
import rosbag
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from PIL import Image

PAPER_DIR = os.path.expanduser('~/Desktop/paper/figures')

BAG_DIR = os.path.expanduser('~/f110_ws/src/Data/bag_files')
MAP_DIR = os.path.expanduser('~/f110_ws/src/F110_ROS_Simulator/maps')
OUT_DIR = os.path.expanduser('~/f110_ws/src/Data/plots&fig')
OUT_FIG4  = os.path.join(OUT_DIR, 'fig4_maps.png')
OUT_FIG8  = os.path.join(OUT_DIR, 'fig8_trajectories.png')

MAP_C = '#1565C0'   # blue   — MAP controller
NN_C  = '#E65100'   # orange — NN controller
RL_C  = '#222222'   # dark   — racing line

# Bags are 100 Hz. min_lap_pts = 70% of (lap_time_at_0.825 × 100 Hz).
# This ensures we're past the halfway point before checking lap closure.
# Overtake ~5.9s, Porto ~6.6s, Hangar ~6.0s, Berlin ~11.5s, F Map ~15.8s
MAPS_0825 = [
    dict(label='Overtake', map_dir='overtake_map', map_file='overtake_map',
         map_bag='run_overtakemap_0.825.bag', nn_bag='nn_overtake_map_0.825.bag',
         n_pts=None, one_lap=True, min_lap_pts=413),
    dict(label='Porto',    map_dir='porto',        map_file='porto',
         map_bag='run_porto_0.825.bag',       nn_bag='nn_porto_0.825.bag',
         n_pts=None, one_lap=True, min_lap_pts=460),
    dict(label='Hangar',   map_dir='hangar',       map_file='hangar',
         map_bag='run_hangar_0.825.bag',      nn_bag='nn_hangar_0.825.bag',
         n_pts=None, one_lap=True, min_lap_pts=421),
    dict(label='Berlin',   map_dir='berlin',       map_file='berlin',
         map_bag='run_berlin_0.825.bag',      nn_bag='nn_berlin_0.825.bag',
         n_pts=None, one_lap=True, min_lap_pts=805),
    dict(label='F Map',    map_dir='f',            map_file='f',
         map_bag='run_f_0.825.bag',           nn_bag='nn_f_0.825.bag',
         n_pts=None, one_lap=True, min_lap_pts=1106),
]

MAPS_0920 = [
    dict(label='Overtake', map_dir='overtake_map', map_file='overtake_map',
         map_bag='map_overtake_0.92.bag',     nn_bag='nn_overtake_0.92.bag',
         n_pts=None, one_lap=True, min_lap_pts=413),
    dict(label='Porto',    map_dir='porto',        map_file='porto',
         map_bag='map_porto_0.92.bag',        nn_bag='nn_porto_0.92.bag',
         n_pts=None, one_lap=True, min_lap_pts=460),
    dict(label='Hangar',   map_dir='hangar',       map_file='hangar',
         map_bag='map_hangar_0.92.bag',       nn_bag='nn_hangar_0.92.bag',
         n_pts=None, one_lap=True, min_lap_pts=421),
    dict(label='Berlin',   map_dir='berlin',       map_file='berlin',
         map_bag='map_berlin_0.92.bag',       nn_bag='nn_berlin_0.92.bag',
         n_pts=None, one_lap=True, min_lap_pts=805),
    dict(label='F Map',    map_dir='f',            map_file='f',
         map_bag='map_f_0.92.bag',            nn_bag='nn_f_0.92.bag',
         n_pts=None, one_lap=True, min_lap_pts=1106),
]

MAPS = MAPS_0825


def read_poses(bag_path, n_max=None, one_lap=False, min_lap_pts=420):
    """Extract (x, y) from /car_state/pose (100 Hz bags).

    Returns (xs, ys, crashed).

    Strategy:
      1. Split the bag into movement runs separated by stationary periods.
         A run ends when the car is stopped for STOP_COUNT consecutive frames
         (crash/reset) or when a position jump > JUMP_THRESH is detected.
      2. For one_lap=True: find the first run whose length exceeds min_lap_pts
         and that returns within LAP_CLOSE_DIST of its starting point.
         If no run completes a lap, return the longest run marked as crashed.
      3. For one_lap=False: return the longest run.
    """
    MOVE_THRESH    = 0.005  # m/frame — below this is considered stationary
    STOP_COUNT     = 100    # consecutive stationary frames = run ended (1 s at 100 Hz)
    LAP_CLOSE_DIST = 0.15   # m — ~2-3 frames at racing speed; gap invisible at figure scale
    JUMP_THRESH    = 1.0    # m — sudden position jump = teleport/reset

    all_poses = []
    with rosbag.Bag(bag_path) as bag:
        for _, msg, _ in bag.read_messages('/car_state/pose'):
            all_poses.append((msg.pose.position.x, msg.pose.position.y))

    if not all_poses:
        return np.array([]), np.array([]), False

    all_poses = np.array(all_poses)
    frame_dists = np.concatenate([[0.0],
                                  np.hypot(np.diff(all_poses[:, 0]),
                                           np.diff(all_poses[:, 1]))])

    # Split into runs
    runs = []   # list of (xs, ys, crashed)
    i = 0
    while i < len(all_poses):
        # Skip stationary frames to find start of next run
        while i < len(all_poses) and frame_dists[i] < MOVE_THRESH:
            i += 1
        if i >= len(all_poses):
            break

        run_xs, run_ys = [], []
        crashed = False
        stop_streak = 0

        while i < len(all_poses):
            d = frame_dists[i]
            if d > JUMP_THRESH:
                crashed = True
                i += 1  # skip past the jump frame to avoid infinite loop
                break

            # Always collect the frame — slow frames must not create gaps
            run_xs.append(all_poses[i, 0])
            run_ys.append(all_poses[i, 1])
            i += 1

            if d < MOVE_THRESH:
                stop_streak += 1
                if stop_streak >= STOP_COUNT:
                    crashed = True
                    # Trim the trailing stationary block (keep just the first stop frame)
                    n_trim = stop_streak - 1
                    if n_trim > 0 and len(run_xs) > n_trim:
                        del run_xs[-n_trim:]
                        del run_ys[-n_trim:]
                    break
            else:
                stop_streak = 0

        if run_xs:
            runs.append((np.array(run_xs), np.array(run_ys), crashed))

    if not runs:
        return np.array([]), np.array([]), False

    if one_lap:
        # Two-pass lap extraction:
        # Pass 1 — find approximate lap end using 0.5 m threshold.
        # Pass 2 — within ±15% of that point, pick the frame closest to xs[0].
        # This gives a near-zero gap regardless of how precisely the car returns.
        APPROX_THRESH = 0.5
        for xs, ys, _ in runs:
            if len(xs) <= min_lap_pts:
                continue
            approx_end = None
            for j in range(min_lap_pts, len(xs)):
                if np.hypot(xs[j] - xs[0], ys[j] - ys[0]) < APPROX_THRESH:
                    approx_end = j
                    break
            if approx_end is None:
                continue
            # Narrow window around the approximate lap end
            win_s = max(min_lap_pts, int(approx_end * 0.85))
            win_e = min(len(xs) - 1, int(approx_end * 1.15))
            dists = np.hypot(xs[win_s:win_e + 1] - xs[0],
                             ys[win_s:win_e + 1] - ys[0])
            best_j = int(np.argmin(dists)) + win_s
            return xs[:best_j + 1], ys[:best_j + 1], False

        # No complete lap — return longest run (shows how far before crash)
        best = max(runs, key=lambda r: len(r[0]))
        xs, ys, crashed = best
        return (xs[:n_max], ys[:n_max], crashed) if n_max else (xs, ys, crashed)

    # one_lap=False — return longest run
    best = max(runs, key=lambda r: len(r[0]))
    xs, ys, crashed = best
    return (xs[:n_max], ys[:n_max], crashed) if n_max else (xs, ys, crashed)


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
    mask = img > 50
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
    fig, axes = plt.subplots(1, 5, figsize=(18, 5), facecolor='white')
    plt.subplots_adjust(left=0.02, right=0.98, top=0.95, bottom=0.12, wspace=0.08)

    for ax, cfg in zip(axes, MAPS):
        img_path = os.path.join(MAP_DIR, cfg['map_dir'], cfg['map_file'] + '.png')
        img_orig = np.array(Image.open(img_path).convert('L'))
        r0, r1, c0, c1 = crop_bounds(img_orig)
        img = 255 - img_orig
        ax.imshow(img[r0:r1, c0:c1], cmap='gray', vmin=0, vmax=255,
                  origin='upper', aspect='equal', alpha=0.35)
        ax.set_facecolor('white')
        ax.axis('off')

    fig.canvas.draw()
    for ax, cfg in zip(axes, MAPS):
        bb = ax.get_position()
        cx = (bb.x0 + bb.x1) / 2
        fig.text(cx, 0.04, cfg['label'], ha='center', va='center',
                 fontsize=18, fontweight='bold', transform=fig.transFigure)

    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(PAPER_DIR, exist_ok=True)
    plt.savefig(OUT_FIG4, dpi=200, bbox_inches='tight', facecolor='white')
    shutil.copy(OUT_FIG4, os.path.join(PAPER_DIR, 'fig4_maps.png'))
    plt.close()
    print(f"Saved -> {OUT_FIG4}")


def _draw_row(axes_row, maps_cfg, row_label):
    """Draw one row of trajectory subplots for a given velocity config."""
    for ax, cfg in zip(axes_row, maps_cfg):
        print(f"  [{row_label}] {cfg['label']} ...", flush=True)

        img_path  = os.path.join(MAP_DIR, cfg['map_dir'], cfg['map_file'] + '.png')
        yaml_path = os.path.join(MAP_DIR, cfg['map_dir'], cfg['map_file'] + '.yaml')
        map_bag   = os.path.join(BAG_DIR, cfg['map_bag'])
        nn_bag    = os.path.join(BAG_DIR, cfg['nn_bag'])

        img = 255 - np.array(Image.open(img_path).convert('L'))
        img_h, img_w = img.shape

        with open(yaml_path) as f:
            ym = yaml.safe_load(f)
        ox, oy, res = ym['origin'][0], ym['origin'][1], ym['resolution']

        def w2p(wx, wy):
            return world_to_pixel(wx, wy, ox, oy, res, img_h)

        rl_x,  rl_y  = read_racing_line(map_bag)
        map_x, map_y, map_crashed = read_poses(map_bag, n_max=cfg['n_pts'],
                                               one_lap=cfg['one_lap'],
                                               min_lap_pts=cfg['min_lap_pts'])
        nn_x,  nn_y,  nn_crashed  = read_poses(nn_bag,  n_max=cfg['n_pts'],
                                               one_lap=cfg['one_lap'],
                                               min_lap_pts=cfg['min_lap_pts'])

        print(f"    MAP: {len(map_x)} pts {'(CRASH)' if map_crashed else '(lap ok)'}", flush=True)
        print(f"    NN:  {len(nn_x)} pts {'(CRASH)' if nn_crashed else '(lap ok)'}", flush=True)


        rl_px,  rl_py  = w2p(rl_x,  rl_y)
        map_px, map_py = w2p(map_x, map_y)
        nn_px,  nn_py  = w2p(nn_x,  nn_y)

        mask = img < 240
        rows = np.where(np.any(mask, axis=1))[0]
        cols = np.where(np.any(mask, axis=0))[0]
        pad = 20
        r0 = max(0,       rows[0]  - pad);  r1 = min(img_h-1, rows[-1] + pad)
        c0 = max(0,       cols[0]  - pad);  c1 = min(img_w-1, cols[-1] + pad)

        ax.imshow(img[r0:r1, c0:c1], cmap='gray', vmin=0, vmax=255,
                  origin='upper', aspect='equal', alpha=0.20)
        ax.plot(rl_px  - c0, rl_py  - r0, '-', color=RL_C,  lw=1.5, alpha=0.50, zorder=2)
        ax.plot(map_px - c0, map_py - r0, '-', color=MAP_C, lw=5.0, alpha=0.70, zorder=3)
        ax.plot(nn_px  - c0, nn_py  - r0, '-', color=NN_C,  lw=2.0, alpha=0.95, zorder=4)

        # Collision markers — X at last recorded point before crash
        if map_crashed and len(map_x) > 0:
            cx, cy = w2p(np.array([map_x[-1]]), np.array([map_y[-1]]))
            ax.plot(cx - c0, cy - r0, 'X', color=MAP_C, markersize=11,
                    markeredgecolor='white', markeredgewidth=1.2, zorder=6)
        if nn_crashed and len(nn_x) > 0:
            cx, cy = w2p(np.array([nn_x[-1]]), np.array([nn_y[-1]]))
            ax.plot(cx - c0, cy - r0, 'X', color=NN_C, markersize=11,
                    markeredgecolor='white', markeredgewidth=1.2, zorder=6)

        ax.set_xlim(0, c1 - c0)
        ax.set_ylim(r1 - r0, 0)
        ax.set_aspect('equal')
        ax.axis('off')


def plot_trajectories():
    """Fig 8 — MAP vs NN trajectory comparison, two velocity profiles (0.825 and 0.92)."""
    fig, axes = plt.subplots(2, 5, figsize=(18, 11), facecolor='white')
    plt.subplots_adjust(left=0.06, right=0.98, top=0.95, bottom=0.12,
                        wspace=0.08, hspace=0.10)

    _draw_row(axes[0], MAPS_0825, 'v=0.825')
    _draw_row(axes[1], MAPS_0920, 'v=0.92')

    # Row labels on the left
    fig.canvas.draw()
    for row_idx, label in enumerate(['v = 0.825', 'v = 0.92']):
        row_axes = axes[row_idx]
        y_positions = [ax.get_position().y0 + ax.get_position().height / 2
                       for ax in row_axes]
        y_mid = np.mean(y_positions)
        fig.text(0.02, y_mid, label, ha='center', va='center',
                 fontsize=13, fontweight='bold', rotation=90,
                 transform=fig.transFigure)

    # Map name labels below the bottom row
    for ax, cfg in zip(axes[1], MAPS_0920):
        bb = ax.get_position()
        cx = (bb.x0 + bb.x1) / 2
        fig.text(cx, 0.06, cfg['label'], ha='center', va='center',
                 fontsize=16, fontweight='bold', transform=fig.transFigure)

    handles = [
        mpatches.Patch(color=RL_C,  label='Racing line (reference)'),
        plt.Line2D([0], [0], color=MAP_C, lw=2.5, label='MAP controller'),
        plt.Line2D([0], [0], color=NN_C,  lw=2.5, label='Our Method (NN)'),
        plt.Line2D([0], [0], color='gray', lw=0, marker='X', markersize=8,
                   markeredgecolor='black', markeredgewidth=0.5,
                   label='Collision point'),
    ]
    fig.legend(handles=handles, loc='lower center', ncol=4, fontsize=11,
               frameon=True, bbox_to_anchor=(0.5, 0.01),
               framealpha=0.95, edgecolor='#cccccc')

    plt.savefig(OUT_FIG8, dpi=200, bbox_inches='tight', facecolor='white')
    shutil.copy(OUT_FIG8, os.path.join(PAPER_DIR, 'fig8_trajectories.png'))
    plt.close()
    print(f"Saved -> {OUT_FIG8}")


if __name__ == '__main__':
    plot_maps()
    plot_trajectories()
