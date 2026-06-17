import os
import shutil
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

PLOTS_DIR = os.path.expanduser('~/f110_ws/src/Data/plots&fig')
PAPER_DIR = os.path.expanduser('~/Desktop/paper/figures')
os.makedirs(PLOTS_DIR, exist_ok=True)
os.makedirs(PAPER_DIR, exist_ok=True)

MAP_C = '#1565C0'
ML_C  = '#E65100'

maps_plain = ['Overtake', 'Porto', 'Hangar', 'Berlin', 'F Map']
speeds     = ['0.60', '0.825', '0.90', '0.92', '0.95', '0.97', '1.00']

cmap = LinearSegmentedColormap.from_list('rc',
       ['#C62828', '#FF6F00', '#FDD835', '#8BC34A', '#1B5E20'])

# Completion rates (%) — rows=maps, cols=speeds [0.60, 0.825, 0.90, 0.92, 0.95, 0.97, 1.00]
map_comp = [
    [100, 100, 100, 100,  20.5, 0.5, 0],   # Overtake
    [100, 100, 100,  16.5, 5.0, 0,   0],   # Porto
    [100, 100, 100, 100,   7.5, 1.0, 0],   # Hangar
    [100,  71.5, 5,  7.5,  6.5, 0.5, 0],  # Berlin
    [100,   1.5, 0,  0,    0,   0,   0],   # F Map
]

# Our Method — leave-one-map-out (each row = that map held out from training)
ml_comp = [
    [100, 100,  3.0,  2.0,  0.5,  0,    0  ],   # Overtake (unseen)
    [100, 100, 100,  100,  100,  100,  100  ],   # Porto (unseen)
    [100, 100, 100,  100,  100,  100,  100  ],   # Hangar (unseen)
    [100, 100, 12.5, 10.5, 35.5, 32.5, 45.5],   # Berlin (unseen)
    [  0, 11.0, 20.0, 18.5,  1.0,  2.5,  1.0],  # F Map (unseen)
]

map_le    = [0.069, 0.060, 0.071, 0.308, 0.298]
ml_le     = [0.184, 0.067, 0.094, 0.178, 0.179]

map_limit = [0.92, 0.90, 0.92, 0.825, 0.60]
ml_limit  = [0.825, 1.00, 1.00, 0.825, None]   # None = NN never ≥50% on F Map

# V1 per-run data on Porto at 0.825 (10 runs)
runs     = list(range(1, 11))
ml_laps  = [6.875, 6.600, 6.600, 6.600, 6.625, 6.625, 6.600, 6.575, 6.625, 6.600]
ml_errs  = [0.079, 0.081, 0.074, 0.082, 0.077, 0.077, 0.080, 0.080, 0.081, 0.079]
map_laps = [6.750, 6.550, 6.525, 6.525, 6.525, 6.525, 6.550, 6.550, 6.525, 6.550]
map_errs = [0.060, 0.057, 0.061, 0.064, 0.059, 0.058, 0.058, 0.061, 0.060, 0.057]


def save(name):
    """Save current figure to both plots&fig/ and paper/figures/."""
    p = os.path.join(PLOTS_DIR, name)
    plt.savefig(p, dpi=220, bbox_inches='tight', facecolor='white')
    shutil.copy(p, os.path.join(PAPER_DIR, name))
    plt.close()
    print(f"Saved {name}")


# Fig 5 — lap-by-lap V1 vs MAP on Porto
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
fig.patch.set_facecolor('white')
ax1.plot(runs, map_laps, 'o-', color=MAP_C, lw=2, ms=7, label='MAP')
ax1.plot(runs, ml_laps,  's-', color=ML_C,  lw=2, ms=7, label='Our Method 2 (V1)')
ax1.set_xlabel('Run', fontsize=12)
ax1.set_ylabel('Duration (s)', fontsize=12)
ax1.set_title('Lap Duration', fontsize=13, fontweight='bold')
ax1.set_xticks(runs)
ax1.set_xlim(0.5, 10.5)
ax1.legend(fontsize=11)
ax1.grid(True, alpha=0.3)

ax2.plot(runs, map_errs, 'o-', color=MAP_C, lw=2, ms=7, label='MAP')
ax2.plot(runs, ml_errs,  's-', color=ML_C,  lw=2, ms=7, label='Our Method 2 (V1)')
ax2.set_xlabel('Run', fontsize=12)
ax2.set_ylabel('Lateral Error (m)', fontsize=12)
ax2.set_title('Lateral Error', fontsize=13, fontweight='bold')
ax2.set_xticks(runs)
ax2.set_xlim(0.5, 10.5)
ax2.legend(fontsize=11)
ax2.grid(True, alpha=0.3)

fig.suptitle('Porto Map (Unseen) — MAP vs Our Method 2 (V1) — Velocity Scale 0.825',
             fontsize=13, fontweight='bold')
plt.tight_layout()
save('fig5_generalization.png')


# Fig 6 — MAP completion heatmap
fig, ax = plt.subplots(figsize=(14, 6))
fig.patch.set_facecolor('white')
data = np.array(map_comp)
im = ax.imshow(data, cmap=cmap, aspect='auto', vmin=0, vmax=100)
ax.set_xticks(range(len(speeds)))
ax.set_xticklabels(speeds, fontsize=13)
ax.set_yticks(range(len(maps_plain)))
ax.set_yticklabels(maps_plain, fontsize=13, fontweight='bold')
ax.set_title('MAP Controller — Lap Completion Rate (%)', fontsize=14, fontweight='bold', pad=12)
ax.set_xlabel('Velocity Scale', fontsize=12)
for i in range(len(maps_plain)):
    for j in range(len(speeds)):
        val = data[i, j]
        ax.text(j, i, f'{val:.0f}%', ha='center', va='center',
                fontsize=11, fontweight='bold', color='white' if val < 30 else 'black')
plt.colorbar(im, ax=ax, shrink=0.9, label='Completion %')
plt.tight_layout()
save('fig6_map_heatmap.png')


# Fig 7 — Our Method completion heatmap
fig, ax = plt.subplots(figsize=(14, 6))
fig.patch.set_facecolor('white')
data = np.array(ml_comp)
im = ax.imshow(data, cmap=cmap, aspect='auto', vmin=0, vmax=100)
ax.set_xticks(range(len(speeds)))
ax.set_xticklabels(speeds, fontsize=13)
ax.set_yticks(range(len(maps_plain)))
ax.set_yticklabels(maps_plain, fontsize=13, fontweight='bold')
ax.set_title('Our Method — Lap Completion Rate (%)\n(Leave-One-Map-Out: each map withheld entirely from training)',
             fontsize=14, fontweight='bold', pad=12)
ax.set_xlabel('Velocity Scale', fontsize=12)
for i in range(len(maps_plain)):
    for j in range(len(speeds)):
        val = data[i, j]
        ax.text(j, i, f'{val:.0f}%', ha='center', va='center',
                fontsize=11, fontweight='bold', color='white' if val < 30 else 'black')
plt.colorbar(im, ax=ax, shrink=0.9, label='Completion %')
plt.tight_layout()
save('fig7_ml_heatmap.png')


# Fig 8 — lateral error bar chart at 0.825
x = np.arange(len(maps_plain))
w = 0.35

fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor('white')
b1 = ax.bar(x - w/2, map_le, w, label='MAP',                       color=MAP_C, edgecolor='black', alpha=0.85)
b2 = ax.bar(x + w/2, ml_le,  w, label='Our Method (Leave-One-Out)', color=ML_C,  edgecolor='black', alpha=0.85)
for bar, val in zip(b1, map_le):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.003,
            f'{val:.3f}m', ha='center', va='bottom', fontsize=10, fontweight='bold', color=MAP_C)
for bar, val in zip(b2, ml_le):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.003,
            f'{val:.3f}m', ha='center', va='bottom', fontsize=10, fontweight='bold', color=ML_C)
ax.set_xticks(x)
ax.set_xticklabels(maps_plain, fontsize=13)
ax.set_title('Average Lateral Error at Velocity Scale 0.825\n(Leave-One-Map-Out: each map withheld entirely from training)',
             fontsize=14, fontweight='bold', pad=12)
ax.set_ylabel('Lateral Error (m)', fontsize=12)
ax.legend(fontsize=12)
ax.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
save('fig8_lateral_error.png')


# Fig 9 — max stable speed bar chart
ml_limit_plot = [v if v is not None else 0 for v in ml_limit]

fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor('white')
b3 = ax.bar(x - w/2, map_limit,     w, label='MAP',                       color=MAP_C, edgecolor='black', alpha=0.85)
b4 = ax.bar(x + w/2, ml_limit_plot, w, label='Our Method (Leave-One-Out)', color=ML_C,  edgecolor='black', alpha=0.85)
for bar, val in zip(b3, map_limit):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.008,
            f'{val}', ha='center', va='bottom', fontsize=11, fontweight='bold', color=MAP_C)
for bar, val, mv in zip(b4, ml_limit, map_limit):
    if val is None:
        ax.text(bar.get_x() + bar.get_width()/2, 0.515,
                'N/A', ha='center', va='bottom', fontsize=11, fontweight='bold', color=ML_C)
    else:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.008,
                f'{val}', ha='center', va='bottom', fontsize=11, fontweight='bold', color=ML_C)
    if val is not None and val > mv:
        ax.annotate('ML wins',
                    xy=(bar.get_x() + bar.get_width()/2, val + 0.04),
                    fontsize=9, ha='center', color='#2E7D32', fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='#E8F5E9',
                              edgecolor='#2E7D32', lw=1.2))
ax.set_xticks(x)
ax.set_xticklabels(maps_plain, fontsize=13)
ax.set_title('Maximum Stable Velocity Scale by Map\n(Leave-One-Map-Out: each map withheld entirely from training)',
             fontsize=14, fontweight='bold', pad=12)
ax.set_ylabel('Max Stable Velocity Scale', fontsize=12)
ax.set_ylim(0.50, 1.20)
ax.axhline(y=1.0, color='green', lw=2, linestyle='--', alpha=0.4, label='Scale 1.0')
ax.legend(fontsize=12)
ax.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
save('fig9_stability_limits.png')
