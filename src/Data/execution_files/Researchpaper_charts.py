import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap

# COLORS AND SHARED DATA
MAP_C = '#1565C0'   # blue  - MAP controller
ML_C  = '#E65100'   # orange - Our Method

maps_short = ['Overtake', 'Porto\n(Unseen)', 'Hangar', 'Berlin', 'F Map']
maps_plain = ['Overtake', 'Porto',           'Hangar', 'Berlin', 'F Map']
speeds     = ['0.60', '0.825', '0.90', '0.92', '0.95', '0.97', '1.00']

cmap = LinearSegmentedColormap.from_list('rc',
       ['#C62828','#FF6F00','#FDD835','#8BC34A','#1B5E20'])

# Completion rates (%) per map per speed
# Rows = maps, Cols = speeds [0.60, 0.825, 0.90, 0.92, 0.95, 0.97, 1.00]
map_comp = [
    [100, 100, 100, 100, 20.5, 0.5,  0],    # Overtake
    [100, 100, 100, 16.5, 5.0, 0,    0],    # Porto
    [100, 100, 100, 100,  7.5, 1.0,  0],    # Hangar
    [100, 71.5, 5,  7.5,  6.5, 0.5,  0],   # Berlin
    [100, 1.5,  0,  0,    0,   0,    0],    # F Map
]
ml_comp = [
    [100, 100, 100, 100,  6.0, 0,    0],    # Overtake
    [100, 100, 100, 100, 100, 100,  100],   # Porto
    [100, 100, 100, 100, 100, 100,  100],   # Hangar
    [100, 100, 35.5, 21.5, 33, 28.5, 64],  # Berlin
    [12.5, 100, 9.5, 2,  4.5,  0,    0],   # F Map
]

# Lateral error at 0.825 per map
map_le = [0.069, 0.060, 0.071, 0.308, 0.298]
ml_le  = [0.074, 0.067, 0.091, 0.239, 0.237]

# Max stable velocity scale per map
map_limit = [0.92, 0.90, 0.92, 0.825, 0.60]
ml_limit  = [0.90, 1.00, 1.00, 0.825, 0.825]

# V1 per-run data on Porto at 0.825 (10 runs)
runs     = list(range(1, 11))
ml_laps  = [6.875, 6.600, 6.600, 6.600, 6.625,
            6.625, 6.600, 6.575, 6.625, 6.600]
ml_errs  = [0.079, 0.081, 0.074, 0.082, 0.077,
            0.077, 0.080, 0.080, 0.081, 0.079]
map_laps = [6.750, 6.550, 6.525, 6.525, 6.525,
            6.525, 6.550, 6.550, 6.525, 6.550]
map_errs = [0.060, 0.057, 0.061, 0.064, 0.059,
            0.058, 0.058, 0.061, 0.060, 0.057]


# FIGURE 4 — Lap-by-lap V1 vs MAP on Porto
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
fig.patch.set_facecolor('white')

ax1.plot(runs, map_laps, 'o-', color=MAP_C, lw=2, ms=7,
         label='MAP', zorder=3)
ax1.plot(runs, ml_laps,  's-', color=ML_C,  lw=2, ms=7,
         label='Our Method 2 (V1)', zorder=3)
ax1.set_xlabel('Run', fontsize=12)
ax1.set_ylabel('Duration (s)', fontsize=12)
ax1.set_title('Lap Duration', fontsize=13, fontweight='bold')
ax1.set_xticks(runs)
ax1.set_xlim(0.5, 10.5)
ax1.legend(fontsize=11)
ax1.grid(True, alpha=0.3)

ax2.plot(runs, map_errs, 'o-', color=MAP_C, lw=2, ms=7,
         label='MAP', zorder=3)
ax2.plot(runs, ml_errs,  's-', color=ML_C,  lw=2, ms=7,
         label='Our Method 2 (V1)', zorder=3)
ax2.set_xlabel('Run', fontsize=12)
ax2.set_ylabel('Lateral Error (m)', fontsize=12)
ax2.set_title('Lateral Error', fontsize=13, fontweight='bold')
ax2.set_xticks(runs)
ax2.set_xlim(0.5, 10.5)
ax2.legend(fontsize=11)
ax2.grid(True, alpha=0.3)

fig.suptitle(
    'Porto Map (Unseen) — MAP vs Our Method 2 (V1) — Velocity Scale 0.825',
    fontsize=13, fontweight='bold')
plt.tight_layout()
plt.savefig('fig4_generalization.png',
            dpi=220, bbox_inches='tight', facecolor='white')
plt.close()
print("Figure 4 (fig4_generalization.png) saved")


# FIGURE 5 — MAP Heatmap
fig, ax = plt.subplots(figsize=(14, 6))
fig.patch.set_facecolor('white')
data = np.array(map_comp)
im = ax.imshow(data, cmap=cmap, aspect='auto', vmin=0, vmax=100)
ax.set_xticks(range(len(speeds)))
ax.set_xticklabels(speeds, fontsize=13)
ax.set_yticks(range(len(maps_short)))
ax.set_yticklabels(maps_short, fontsize=13, fontweight='bold')
ax.set_title('MAP Controller — Lap Completion Rate (%)',
             fontsize=14, fontweight='bold', pad=12)
ax.set_xlabel('Velocity Scale', fontsize=12)
for i in range(len(maps_short)):
    for j in range(len(speeds)):
        val = data[i, j]
        c = 'white' if val < 30 else 'black'
        ax.text(j, i, f'{val:.0f}%', ha='center', va='center',
                fontsize=11, fontweight='bold', color=c)
plt.colorbar(im, ax=ax, shrink=0.9, label='Completion %')
plt.tight_layout()
plt.savefig('fig5_map_heatmap.png',
            dpi=220, bbox_inches='tight', facecolor='white')
plt.close()
print("Figure 5 (fig5_map_heatmap.png) saved")


# FIGURE 6 — ML Heatmap 
fig, ax = plt.subplots(figsize=(14, 6))
fig.patch.set_facecolor('white')
data = np.array(ml_comp)
im = ax.imshow(data, cmap=cmap, aspect='auto', vmin=0, vmax=100)
ax.set_xticks(range(len(speeds)))
ax.set_xticklabels(speeds, fontsize=13)
ax.set_yticks(range(len(maps_short)))
ax.set_yticklabels(maps_short, fontsize=13, fontweight='bold')
ax.set_title('Our Method — Lap Completion Rate (%)',
             fontsize=14, fontweight='bold', pad=12)
ax.set_xlabel('Velocity Scale', fontsize=12)
for i in range(len(maps_short)):
    for j in range(len(speeds)):
        val = data[i, j]
        c = 'white' if val < 30 else 'black'
        ax.text(j, i, f'{val:.0f}%', ha='center', va='center',
                fontsize=11, fontweight='bold', color=c)
plt.colorbar(im, ax=ax, shrink=0.9, label='Completion %')
plt.tight_layout()
plt.savefig('fig6_ml_heatmap.png',
            dpi=220, bbox_inches='tight', facecolor='white')
plt.close()
print("Figure 6 (fig6_ml_heatmap.png) saved")


# FIGURE 7 — Lateral Error at 0.825
x = np.arange(len(maps_plain))
w = 0.35

fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor('white')
b1 = ax.bar(x-w/2, map_le, w, label='MAP',
            color=MAP_C, edgecolor='black', alpha=0.85)
b2 = ax.bar(x+w/2, ml_le,  w, label='Our Method 2 (V2)',
            color=ML_C,  edgecolor='black', alpha=0.85)
for bar, val in zip(b1, map_le):
    ax.text(bar.get_x()+bar.get_width()/2,
            bar.get_height()+0.003, f'{val:.3f}m',
            ha='center', va='bottom', fontsize=10,
            fontweight='bold', color=MAP_C)
for bar, val in zip(b2, ml_le):
    ax.text(bar.get_x()+bar.get_width()/2,
            bar.get_height()+0.003, f'{val:.3f}m',
            ha='center', va='bottom', fontsize=10,
            fontweight='bold', color=ML_C)
ax.set_xticks(x)
ax.set_xticklabels(maps_plain, fontsize=13)
ax.set_title('Average Lateral Error at Velocity Scale 0.825',
             fontsize=14, fontweight='bold', pad=12)
ax.set_ylabel('Lateral Error (m)', fontsize=12)
ax.legend(fontsize=12)
ax.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig('fig7_lateral_error.png',
            dpi=220, bbox_inches='tight', facecolor='white')
plt.close()
print("Figure 7 (fig7_lateral_error.png) saved")


# FIGURE 8 — Stability Limits
fig, ax = plt.subplots(figsize=(12, 6))
fig.patch.set_facecolor('white')
b3 = ax.bar(x-w/2, map_limit, w, label='MAP',
            color=MAP_C, edgecolor='black', alpha=0.85)
b4 = ax.bar(x+w/2, ml_limit,  w, label='Our Method 2 (V2)',
            color=ML_C,  edgecolor='black', alpha=0.85)
for bar, val in zip(b3, map_limit):
    ax.text(bar.get_x()+bar.get_width()/2,
            bar.get_height()+0.008, f'{val}',
            ha='center', va='bottom', fontsize=11,
            fontweight='bold', color=MAP_C)
for bar, val, mv in zip(b4, ml_limit, map_limit):
    ax.text(bar.get_x()+bar.get_width()/2,
            bar.get_height()+0.008, f'{val}',
            ha='center', va='bottom', fontsize=11,
            fontweight='bold', color=ML_C)
    if val > mv:
        ax.annotate('ML wins',
                    xy=(bar.get_x()+bar.get_width()/2, val+0.04),
                    fontsize=9, ha='center', color='#2E7D32',
                    fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.2',
                              facecolor='#E8F5E9',
                              edgecolor='#2E7D32', lw=1.2))
ax.set_xticks(x)
ax.set_xticklabels(maps_plain, fontsize=13)
ax.set_title('Maximum Stable Velocity Scale by Map',
             fontsize=14, fontweight='bold', pad=12)
ax.set_ylabel('Max Stable Velocity Scale', fontsize=12)
ax.set_ylim(0.50, 1.20)
ax.axhline(y=1.0, color='green', lw=2,
           linestyle='--', alpha=0.4, label='Scale 1.0')
ax.legend(fontsize=12)
ax.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig('fig8_stability_limits.png',
            dpi=220, bbox_inches='tight', facecolor='white')
plt.close()
print("Figure 8 (fig8_stability_limits.png) saved")