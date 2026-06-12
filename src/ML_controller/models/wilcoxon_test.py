from scipy import stats
import numpy as np
import matplotlib.pyplot as plt

# =============================================================
# YOUR RESULTS
# =============================================================

# Unseen Map results (velocity_scale = 0.825)

# MAP Controller - Porto Map - Velocity Scale 0.825 - 20 Laps
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

# ML Controller (Our Method 2 V2) - Porto Map - Velocity Scale 0.825 - 20 Laps
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

# =============================================================
# WILCOXON SIGNED-RANK TEST
# =============================================================

# Lateral Error
stat_error, p_error = stats.wilcoxon(
    map_lateral_errors,
    ml_lateral_errors,
    alternative='two-sided'
)

# Lap Time
stat_time, p_time = stats.wilcoxon(
    map_lap_times,
    ml_lap_times,
    alternative='two-sided'
)

# =============================================================
# PRINT RESULTS
# =============================================================

print("=" * 60)
print("        WILCOXON SIGNED-RANK TEST RESULTS")
print("=" * 60)

print("\n📊 Lateral Error")
print(f"MAP Mean        : {np.mean(map_lateral_errors):.4f} m")
print(f"ML Mean         : {np.mean(ml_lateral_errors):.4f} m")
print(f"Wilcoxon Stat   : {stat_error:.4f}")
print(f"p-value         : {p_error:.6f}")

if p_error < 0.05:
    print("Result          : ✅ Significant Difference")
else:
    print("Result          : ❌ Not Significant")

print("\n⏱️ Lap Time")
print(f"MAP Mean        : {np.mean(map_lap_times):.4f} s")
print(f"ML Mean         : {np.mean(ml_lap_times):.4f} s")
print(f"Wilcoxon Stat   : {stat_time:.4f}")
print(f"p-value         : {p_time:.6f}")

if p_time < 0.05:
    print("Result          : ✅ Significant Difference")
else:
    print("Result          : ❌ Not Significant")

# =============================================================
# EFFECT SIZE — COHEN'S D
# =============================================================

def cohens_d(group1, group2):
    diff   = np.mean(group1) - np.mean(group2)
    pooled = np.sqrt(
        (np.std(group1)**2 + np.std(group2)**2) / 2
    )
    return abs(diff / pooled)

d_error = cohens_d(map_lateral_errors, ml_lateral_errors)
d_time  = cohens_d(map_lap_times, ml_lap_times)

print("\n📏 EFFECT SIZE (Cohen's d)")

print(f"Lateral Error : {d_error:.4f}", end=" → ")
if d_error < 0.2:
    print("Negligible")
elif d_error < 0.5:
    print("Small")
elif d_error < 0.8:
    print("Medium")
else:
    print("Large")

print(f"Lap Time      : {d_time:.4f}", end=" → ")
if d_time < 0.2:
    print("Negligible")
elif d_time < 0.5:
    print("Small")
elif d_time < 0.8:
    print("Medium")
else:
    print("Large")

# =============================================================
# VISUALIZATION
# 2x2 Figure:
#   1. Paired Line Plot (Lateral Error)
#   2. Box Plot        (Lateral Error)
#   3. Paired Line Plot (Lap Time)
#   4. Box Plot         (Lap Time)
# =============================================================

fig, axes = plt.subplots(2, 2, figsize=(14, 10))

fig.suptitle(
    'MAP vs ML Controller — Wilcoxon Statistical Comparison',
    fontsize=16,
    fontweight='bold'
)

# =============================================================
# PLOT 1 — PAIRED LINE PLOT (LATERAL ERROR)
# =============================================================

ax = axes[0, 0]

for i in range(len(map_lateral_errors)):
    ax.plot(
        ['MAP', 'ML'],
        [map_lateral_errors[i], ml_lateral_errors[i]],
        marker='o'
    )

ax.set_title(
    f'Paired Comparison — Lateral Error\np = {p_error:.6f}'
)

ax.set_ylabel('Lateral Error (m)')
ax.grid(True)

# Mean lines
ax.hlines(
    np.mean(map_lateral_errors),
    xmin=-0.1,
    xmax=0.1,
    linewidth=4,
    label='MAP Mean'
)

ax.hlines(
    np.mean(ml_lateral_errors),
    xmin=0.9,
    xmax=1.1,
    linewidth=4,
    label='ML Mean'
)

ax.legend()

# =============================================================
# PLOT 2 — BOX PLOT (LATERAL ERROR)
# =============================================================

ax = axes[0, 1]

ax.boxplot(
    [map_lateral_errors, ml_lateral_errors],
    labels=['MAP', 'ML'],
    patch_artist=True
)

ax.set_title(
    f'Box Plot — Lateral Error\np = {p_error:.6f}'
)

ax.set_ylabel('Lateral Error (m)')
ax.grid(True)

# =============================================================
# PLOT 3 — PAIRED LINE PLOT (LAP TIME)
# =============================================================

ax = axes[1, 0]

for i in range(len(map_lap_times)):
    ax.plot(
        ['MAP', 'ML'],
        [map_lap_times[i], ml_lap_times[i]],
        marker='o'
    )

ax.set_title(
    f'Paired Comparison — Lap Time\np = {p_time:.6f}'
)

ax.set_ylabel('Lap Time (s)')
ax.grid(True)

# Mean lines
ax.hlines(
    np.mean(map_lap_times),
    xmin=-0.1,
    xmax=0.1,
    linewidth=4,
    label='MAP Mean'
)

ax.hlines(
    np.mean(ml_lap_times),
    xmin=0.9,
    xmax=1.1,
    linewidth=4,
    label='ML Mean'
)

ax.legend()

# =============================================================
# PLOT 4 — BOX PLOT (LAP TIME)
# =============================================================

ax = axes[1, 1]

ax.boxplot(
    [map_lap_times, ml_lap_times],
    labels=['MAP', 'ML'],
    patch_artist=True
)

ax.set_title(
    f'Box Plot — Lap Time\np = {p_time:.6f}'
)

ax.set_ylabel('Lap Time (s)')
ax.grid(True)

# =============================================================
# SAVE + SHOW
# =============================================================

plt.tight_layout()

plt.savefig(
    "wilcoxon_paired_test_final_portomap.png",
    dpi=300,
    bbox_inches='tight'
)


plt.show()

print("\n✅ Figure saved as:")
print("wilcoxon_paired_test_finl_portomap.png")