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

map_le = [0.069, 0.060, 0.071, 0.308, 0.298]
ml_le  = [0.184, 0.067, 0.094, 0.178, 0.179]


def save(name):
    """Save current figure to both plots&fig/ and paper/figures/."""
    p = os.path.join(PLOTS_DIR, name)
    plt.savefig(p, dpi=220, bbox_inches='tight', facecolor='white')
    shutil.copy(p, os.path.join(PAPER_DIR, name))
    plt.close()
    print(f"Saved {name}")


# Fig 5 — MAP completion heatmap
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
        txt_color = 'white' if (val < 30 or val > 75) else 'black'
        ax.text(j, i, f'{val:.0f}%', ha='center', va='center',
                fontsize=11, fontweight='bold', color=txt_color)
plt.colorbar(im, ax=ax, shrink=0.9, label='Completion %')
plt.tight_layout()
save('fig5_map_heatmap.png')


# Fig 6 — Our Method completion heatmap
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
        txt_color = 'white' if (val < 30 or val > 75) else 'black'
        ax.text(j, i, f'{val:.0f}%', ha='center', va='center',
                fontsize=11, fontweight='bold', color=txt_color)
plt.colorbar(im, ax=ax, shrink=0.9, label='Completion %')
plt.tight_layout()
save('fig6_ml_heatmap.png')


# Fig 7 — lateral error bar chart at 0.825
x = np.arange(len(maps_plain))
w = 0.35

fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor('white')
b1 = ax.bar(x - w/2, map_le, w, label='MAP',                       color=MAP_C, edgecolor='black', alpha=0.85)
b2 = ax.bar(x + w/2, ml_le,  w, label='Our Method (Leave-One-Out)', color=ML_C,  edgecolor='black', alpha=0.85)
for bar, val in zip(b1, map_le):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.003,
            f'{val:.3f}m', ha='center', va='bottom', fontsize=12, fontweight='bold', color=MAP_C)
for bar, val in zip(b2, ml_le):
    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.003,
            f'{val:.3f}m', ha='center', va='bottom', fontsize=12, fontweight='bold', color=ML_C)
ax.set_xticks(x)
ax.set_xticklabels(maps_plain, fontsize=13)
ax.set_title('Average Lateral Error at Velocity Scale 0.825\n(Leave-One-Map-Out: each map withheld entirely from training)',
             fontsize=14, fontweight='bold', pad=12)
ax.set_ylabel('Lateral Error (m)', fontsize=12)
ax.legend(fontsize=12)
ax.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
save('fig7_lateral_error.png')
