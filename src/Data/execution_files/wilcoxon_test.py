import os
from scipy import stats
import numpy as np
import matplotlib.pyplot as plt

OUT_PATH = os.path.expanduser(
    '~/f110_ws/src/Data/plots&fig/wilcoxon_paired_test_final_portomap.png'
)

# Porto map, velocity scale 0.825, 20 laps each
map_lateral_errors = [
    0.059, 0.061, 0.063, 0.062, 0.062,
    0.059, 0.060, 0.060, 0.060, 0.059,
    0.061, 0.062, 0.060, 0.057, 0.061,
    0.059, 0.060, 0.061, 0.058, 0.060
]

map_lap_times = [
    6.750, 6.550, 6.525, 6.525, 6.525,
    6.550, 6.550, 6.525, 6.525, 6.525,
    6.550, 6.550, 6.550, 6.550, 6.525,
    6.525, 6.550, 6.550, 6.550, 6.550
]

ml_lateral_errors = [
    0.061, 0.071, 0.070, 0.072, 0.070,
    0.069, 0.071, 0.072, 0.070, 0.069,
    0.067, 0.069, 0.070, 0.069, 0.070,
    0.070, 0.071, 0.071, 0.067, 0.069
]

ml_lap_times = [
    6.750, 6.575, 6.575, 6.549, 6.550,
    6.574, 6.600, 6.575, 6.550, 6.575,
    6.600, 6.575, 6.600, 6.550, 6.550,
    6.575, 6.575, 6.575, 6.550, 6.550
]

# Wilcoxon signed-rank test (non-parametric, paired)
stat_error, p_error = stats.wilcoxon(map_lateral_errors, ml_lateral_errors, alternative='two-sided')
stat_time,  p_time  = stats.wilcoxon(map_lap_times,      ml_lap_times,      alternative='two-sided')

print("=" * 60)
print("        WILCOXON SIGNED-RANK TEST RESULTS")
print("=" * 60)

print(f"\nLateral Error")
print(f"  MAP mean : {np.mean(map_lateral_errors):.4f} m")
print(f"  ML mean  : {np.mean(ml_lateral_errors):.4f} m")
print(f"  stat={stat_error:.4f}  p={p_error:.6f}")
print(f"  {'Significant difference' if p_error < 0.05 else 'No significant difference'}")

print(f"\nLap Time")
print(f"  MAP mean : {np.mean(map_lap_times):.4f} s")
print(f"  ML mean  : {np.mean(ml_lap_times):.4f} s")
print(f"  stat={stat_time:.4f}  p={p_time:.6f}")
print(f"  {'Significant difference' if p_time < 0.05 else 'No significant difference'}")


def cohens_d(a, b):
    diff = np.mean(a) - np.mean(b)
    pooled_std = np.sqrt((np.std(a)**2 + np.std(b)**2) / 2)
    return abs(diff / pooled_std)

def effect_label(d):
    if d < 0.2: return "Negligible"
    if d < 0.5: return "Small"
    if d < 0.8: return "Medium"
    return "Large"

d_error = cohens_d(map_lateral_errors, ml_lateral_errors)
d_time  = cohens_d(map_lap_times, ml_lap_times)

print(f"\nEffect size (Cohen's d)")
print(f"  Lateral error : {d_error:.4f} ({effect_label(d_error)})")
print(f"  Lap time      : {d_time:.4f}  ({effect_label(d_time)})")


fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('MAP vs ML Controller — Wilcoxon Statistical Comparison',
             fontsize=16, fontweight='bold')

for row, (map_data, ml_data, ylabel, stat, p) in enumerate([
    (map_lateral_errors, ml_lateral_errors, 'Lateral Error (m)', stat_error, p_error),
    (map_lap_times,      ml_lap_times,      'Lap Time (s)',      stat_time,  p_time),
]):
    # Paired line plot
    ax = axes[row, 0]
    for i in range(len(map_data)):
        ax.plot(['MAP', 'ML'], [map_data[i], ml_data[i]], marker='o', alpha=0.6)
    ax.hlines(np.mean(map_data), -0.1, 0.1, lw=4, label='MAP mean')
    ax.hlines(np.mean(ml_data),   0.9, 1.1, lw=4, label='ML mean')
    ax.set_title(f'Paired Comparison — {ylabel.split(" (")[0]}\np = {p:.6f}')
    ax.set_ylabel(ylabel)
    ax.legend()
    ax.grid(True)

    # Box plot
    ax = axes[row, 1]
    ax.boxplot([map_data, ml_data], labels=['MAP', 'ML'], patch_artist=True)
    ax.set_title(f'Box Plot — {ylabel.split(" (")[0]}\np = {p:.6f}')
    ax.set_ylabel(ylabel)
    ax.grid(True)

plt.tight_layout()
plt.savefig(OUT_PATH, dpi=300, bbox_inches='tight')
print(f"\nSaved -> {OUT_PATH}")
plt.show()
