#!/usr/bin/env python3

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import joblib
import time
import warnings
warnings.filterwarnings('ignore')

from sklearn.model_selection   import train_test_split
from sklearn.preprocessing     import StandardScaler
from sklearn.ensemble          import RandomForestRegressor
from sklearn.svm               import SVR
from sklearn.gaussian_process  import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern
from sklearn.metrics           import mean_squared_error, mean_absolute_error, r2_score
from xgboost                   import XGBRegressor

# =============================================================
# STEP 1: LOAD DATA
# =============================================================
df = pd.read_csv("/home/sanjeev/f110_ws/src/Data/data_files/method2V1V2_traintest_porto.csv")
print(f"✅ Loaded | Rows: {len(df)}")

X = df[["d_m", "heading_error", "kappa", "vx", "kappa_lookahead"]].values
y = df["steering"].values

print(f"   X shape : {X.shape}")
print(f"   y shape : {y.shape}")

# =============================================================
# STEP 2: NORMALIZE
# Same scaler for all models — fair comparison
# =============================================================
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
print(f"✅ Data normalized")

# =============================================================
# STEP 3: TRAIN/VAL SPLIT
# Full data for RF and XGBoost
# Subset for SVM and GP (computationally too expensive)
# =============================================================
X_train_full, X_test, y_train_full, y_test = train_test_split(
    X_scaled, y,
    test_size    = 0.2,
    random_state = 42,
    shuffle      = True
)

# Subset for slow models
SUBSET_SIZE  = 5000
idx_subset   = np.random.choice(len(X_train_full),
                                 SUBSET_SIZE, replace=False)
X_train_sub  = X_train_full[idx_subset]
y_train_sub  = y_train_full[idx_subset]

print(f"\n   Full train  : {len(X_train_full)} samples → RF, XGBoost")
print(f"   Subset train: {len(X_train_sub)} samples  → SVM, GP")
print(f"   Test        : {len(X_test)} samples")

# =============================================================
# STEP 4: EVALUATION FUNCTION
# =============================================================
def evaluate_model(name, y_true, y_pred, train_time, inf_time):
    """
    MSE  — Mean Squared Error
    RMSE — Root MSE in radians
    MAE  — Mean Absolute Error
    R2   — How well model explains variance (1.0 = perfect)
    """
    mse  = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    mae  = mean_absolute_error(y_true, y_pred)
    r2   = r2_score(y_true, y_pred)

    print(f"\n{'─'*55}")
    print(f"  {name}")
    print(f"{'─'*55}")
    print(f"  MSE            : {mse:.6f}")
    print(f"  RMSE           : {rmse:.4f} rad")
    print(f"  MAE            : {mae:.4f} rad")
    print(f"  R2 Score       : {r2:.4f}")
    print(f"  Train Time     : {train_time:.2f} s")
    print(f"  Inference Time : {inf_time:.4f} ms per sample")

    return {
        'name'           : name,
        'mse'            : mse,
        'rmse'           : rmse,
        'mae'            : mae,
        'r2'             : r2,
        'train_time'     : train_time,
        'inference_time' : inf_time,
        'predictions'    : y_pred
    }

# =============================================================
# STEP 5: TRAIN ALL 4 MODELS
# =============================================================
all_results = {}

# ─────────────────────────────────────────────────────────────
# MODEL 1: RANDOM FOREST
# Ensemble of decision trees
# Trained on FULL data
# ─────────────────────────────────────────────────────────────
print(f"\n{'='*55}")
print(f"  Training: RANDOM FOREST")
print(f"{'='*55}")

start    = time.time()
rf_model = RandomForestRegressor(
    n_estimators      = 100,
    max_depth         = 15,
    min_samples_split = 5,
    n_jobs            = -1,
    random_state      = 42
)
rf_model.fit(X_train_full, y_train_full)
rf_train_time = time.time() - start

start_inf    = time.perf_counter()
rf_pred      = rf_model.predict(X_test)
end_inf      = time.perf_counter()
rf_inf_time  = ((end_inf - start_inf) / len(X_test)) * 1000

joblib.dump(rf_model, "model_random_forest.pth")
all_results['Random Forest'] = evaluate_model(
    'Random Forest', y_test, rf_pred,
    rf_train_time, rf_inf_time
)
print(f"  ✅ Saved: model_random_forest.pth")

# ─────────────────────────────────────────────────────────────
# MODEL 2: XGBOOST
# Gradient boosting trees
# Trained on FULL data
# ─────────────────────────────────────────────────────────────
print(f"\n{'='*55}")
print(f"  Training: XGBOOST")
print(f"{'='*55}")

start     = time.time()
xgb_model = XGBRegressor(
    n_estimators     = 300,
    max_depth        = 6,
    learning_rate    = 0.05,
    subsample        = 0.8,
    colsample_bytree = 0.8,
    random_state     = 42,
    verbosity        = 0,
    n_jobs           = -1
)
xgb_model.fit(
    X_train_full, y_train_full,
    eval_set = [(X_test, y_test)],
    verbose  = False
)
xgb_train_time = time.time() - start

start_inf    = time.perf_counter()
xgb_pred     = xgb_model.predict(X_test)
end_inf      = time.perf_counter()
xgb_inf_time = ((end_inf - start_inf) / len(X_test)) * 1000

joblib.dump(xgb_model, "model_xgboost.pth")
all_results['XGBoost'] = evaluate_model(
    'XGBoost', y_test, xgb_pred,
    xgb_train_time, xgb_inf_time
)
print(f"  ✅ Saved: model_xgboost.pth")

# ─────────────────────────────────────────────────────────────
# MODEL 3: SVM
# Support Vector Machine with RBF kernel
# Trained on SUBSET — too slow on full 79k data
# ─────────────────────────────────────────────────────────────
print(f"\n{'='*55}")
print(f"  Training: SVM (subset of {SUBSET_SIZE} samples)")
print(f"{'='*55}")
print(f"  Note: SVM is O(n²) — subset used for speed")

start     = time.time()
svm_model = SVR(
    kernel  = 'rbf',
    C       = 10.0,
    epsilon = 0.001,
    gamma   = 'scale'
)
svm_model.fit(X_train_sub, y_train_sub)
svm_train_time = time.time() - start

start_inf    = time.perf_counter()
svm_pred     = svm_model.predict(X_test)
end_inf      = time.perf_counter()
svm_inf_time = ((end_inf - start_inf) / len(X_test)) * 1000

joblib.dump(svm_model, "model_svm.pth")
all_results['SVM (RBF)'] = evaluate_model(
    'SVM (RBF)', y_test, svm_pred,
    svm_train_time, svm_inf_time
)
print(f"  ✅ Saved: model_svm.pth")

# ─────────────────────────────────────────────────────────────
# MODEL 4: GAUSSIAN PROCESS
# Probabilistic model with uncertainty estimates
# Trained on SUBSET — too slow on full data
# ─────────────────────────────────────────────────────────────
print(f"\n{'='*55}")
print(f"  Training: GAUSSIAN PROCESS (subset of {SUBSET_SIZE} samples)")
print(f"{'='*55}")
print(f"  Note: GP is O(n³) — subset used for speed")

kernel   = ConstantKernel(1.0) * Matern(length_scale=1.0, nu=1.5)
start    = time.time()
gp_model = GaussianProcessRegressor(
    kernel               = kernel,
    alpha                = 1e-3,
    normalize_y          = True,
    n_restarts_optimizer = 2
)
gp_model.fit(X_train_sub, y_train_sub)
gp_train_time = time.time() - start

start_inf    = time.perf_counter()
gp_pred      = gp_model.predict(X_test)
end_inf      = time.perf_counter()
gp_inf_time  = ((end_inf - start_inf) / len(X_test)) * 1000

joblib.dump(gp_model, "model_gp.pth")
all_results['Gaussian Process'] = evaluate_model(
    'Gaussian Process', y_test, gp_pred,
    gp_train_time, gp_inf_time
)
print(f"  ✅ Saved: model_gp.pth")

# =============================================================
# STEP 6: FINAL COMPARISON TABLE
# =============================================================
best_model = min(all_results, key=lambda x: all_results[x]['mse'])
sorted_results = sorted(all_results.items(),
                         key=lambda x: x[1]['mse'])

print(f"\n{'='*75}")
print(f"  FINAL COMPARISON — 4 ML MODELS")
print(f"{'='*75}")
print(f"{'Model':<20} {'MSE':>10} {'RMSE':>10} {'MAE':>10} "
      f"{'R2':>8} {'Infer(ms)':>12} {'Train(s)':>10}")
print(f"{'-'*75}")

for name, res in sorted_results:
    marker = "  ★" if name == best_model else ""
    print(f"{name:<20} {res['mse']:>10.6f} "
          f"{res['rmse']:>10.4f} "
          f"{res['mae']:>10.4f} "
          f"{res['r2']:>8.4f} "
          f"{res['inference_time']:>12.4f} "
          f"{res['train_time']:>10.2f}"
          f"{marker}")

print(f"\n  ★ Best model : {best_model}")

# =============================================================
# STEP 7: PLOTS
# =============================================================
model_names = list(all_results.keys())
colors_map  = {
    'Random Forest'    : '#2196F3',
    'XGBoost'          : '#FF5722',
    'SVM (RBF)'        : '#4CAF50',
    'Gaussian Process' : '#9C27B0'
}

fig, axes = plt.subplots(2, 3, figsize=(18, 11))
fig.suptitle('Classical ML Models Comparison — Steering Prediction',
             fontsize=14, fontweight='bold')
axes = axes.flatten()

# ── Plot 1: MSE ──
ax = axes[0]
mse_vals = [all_results[m]['mse'] for m in model_names]
bars     = ax.bar(model_names, mse_vals,
                  color=[colors_map[m] for m in model_names],
                  edgecolor='black', alpha=0.85)
for bar, val in zip(bars, mse_vals):
    ax.text(bar.get_x() + bar.get_width()/2,
            bar.get_height() + max(mse_vals)*0.01,
            f'{val:.6f}', ha='center', va='bottom', fontsize=8)
best_idx = model_names.index(best_model)
bars[best_idx].set_edgecolor('red')
bars[best_idx].set_linewidth(3)
ax.set_title('MSE (Lower = Better)', fontweight='bold')
ax.set_ylabel('Mean Squared Error')
ax.set_xticklabels(model_names, rotation=15, ha='right')
ax.grid(True, alpha=0.3, axis='y')

# ── Plot 2: RMSE ──
ax = axes[1]
rmse_vals = [all_results[m]['rmse'] for m in model_names]
bars      = ax.bar(model_names, rmse_vals,
                   color=[colors_map[m] for m in model_names],
                   edgecolor='black', alpha=0.85)
for bar, val in zip(bars, rmse_vals):
    ax.text(bar.get_x() + bar.get_width()/2,
            bar.get_height() + max(rmse_vals)*0.01,
            f'{val:.4f}', ha='center', va='bottom', fontsize=8)
ax.set_title('RMSE in radians (Lower = Better)', fontweight='bold')
ax.set_ylabel('RMSE (rad)')
ax.set_xticklabels(model_names, rotation=15, ha='right')
ax.grid(True, alpha=0.3, axis='y')

# ── Plot 3: R2 Score ──
ax = axes[2]
r2_vals = [all_results[m]['r2'] for m in model_names]
bars    = ax.bar(model_names, r2_vals,
                 color=[colors_map[m] for m in model_names],
                 edgecolor='black', alpha=0.85)
for bar, val in zip(bars, r2_vals):
    ax.text(bar.get_x() + bar.get_width()/2,
            bar.get_height() + 0.005,
            f'{val:.4f}', ha='center', va='bottom', fontsize=8)
ax.axhline(y=1.0, color='green', linewidth=1.5,
           linestyle='--', alpha=0.6, label='Perfect = 1.0')
ax.set_title('R2 Score (Higher = Better)', fontweight='bold')
ax.set_ylabel('R2 Score')
ax.set_xticklabels(model_names, rotation=15, ha='right')
ax.legend()
ax.grid(True, alpha=0.3, axis='y')

# ── Plot 4: Inference Time ──
ax = axes[3]
inf_vals = [all_results[m]['inference_time'] for m in model_names]
bars     = ax.bar(model_names, inf_vals,
                  color=[colors_map[m] for m in model_names],
                  edgecolor='black', alpha=0.85)
for bar, val in zip(bars, inf_vals):
    ax.text(bar.get_x() + bar.get_width()/2,
            bar.get_height() + max(inf_vals)*0.01,
            f'{val:.4f}ms', ha='center', va='bottom', fontsize=8)
ax.axhline(y=1.0, color='red', linewidth=1.5,
           linestyle='--', alpha=0.6,
           label='Real-time limit ~1ms')
ax.set_title('Inference Time (Lower = Better)', fontweight='bold')
ax.set_ylabel('Time per sample (ms)')
ax.set_xticklabels(model_names, rotation=15, ha='right')
ax.legend()
ax.grid(True, alpha=0.3, axis='y')

# ── Plot 5: Predicted vs Actual ──
ax = axes[4]
sample_idx = np.random.choice(len(y_test), 300, replace=False)
for name in model_names:
    pred = all_results[name]['predictions']
    ax.scatter(y_test[sample_idx], pred[sample_idx],
               alpha=0.4, s=15,
               color=colors_map[name], label=name)
ax.plot([-0.4, 0.4], [-0.4, 0.4],
        'k--', linewidth=2, label='Perfect prediction')
ax.set_title('Predicted vs Actual Steering\n(300 samples)',
             fontweight='bold')
ax.set_xlabel('Actual Steering (rad)')
ax.set_ylabel('Predicted Steering (rad)')
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3)

# ── Plot 6: Normalized Summary ──
ax = axes[5]
metrics = ['MSE\n(lower)', 'RMSE\n(lower)', 'MAE\n(lower)', 'R2\n(higher)']
x_pos   = np.arange(len(metrics))
width   = 0.18

for i, name in enumerate(model_names):
    res    = all_results[name]
    mse_n  = 1-(res['mse']  / max(r['mse']  for r in all_results.values()))
    rmse_n = 1-(res['rmse'] / max(r['rmse'] for r in all_results.values()))
    mae_n  = 1-(res['mae']  / max(r['mae']  for r in all_results.values()))
    r2_n   = res['r2'] / max(r['r2'] for r in all_results.values())
    vals   = [mse_n, rmse_n, mae_n, r2_n]
    ax.bar(x_pos + i*width, vals, width,
           label=name, color=colors_map[name],
           edgecolor='black', alpha=0.85)

ax.set_title('Normalized Performance\n(Higher = Better for all)',
             fontweight='bold')
ax.set_xticks(x_pos + width * 1.5)
ax.set_xticklabels(metrics)
ax.set_ylabel('Normalized Score (0-1)')
ax.legend(fontsize=8)
ax.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig("ml_models_comparison.png", dpi=150, bbox_inches='tight')
plt.show()
print("\n✅ Plot saved as ml_models_comparison.png")

# =============================================================
# STEP 8: REAL TIME CHECK
# =============================================================
print(f"\n{'='*55}")
print(f"  REAL-TIME CHECK (40Hz = 25ms budget per loop)")
print(f"{'='*55}")
print(f"{'Model':<20} {'Inference':>12} {'Real-time?':>12}")
print(f"{'-'*48}")
for name, res in sorted_results:
    feasible = "YES" if res['inference_time'] < 1.0 else "NO"
    print(f"{name:<20} {res['inference_time']:>10.4f}ms {feasible:>12}")