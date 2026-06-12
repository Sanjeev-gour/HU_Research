#!/usr/bin/env python3

import numpy as np
import pandas as pd
import torch
import joblib
import time
import matplotlib.pyplot as plt

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    mean_squared_error,
    mean_absolute_error,
    r2_score
)

# ============================================================
# EXTREME LEARNING MACHINE (ELM)
# ============================================================

class ELMRegressor:

    def __init__(
        self,
        input_size,
        hidden_size=128,
        activation='relu',
        reg_lambda=1e-3,
        random_state=42
    ):

        np.random.seed(random_state)

        self.input_size = input_size
        self.hidden_size = hidden_size
        self.activation = activation
        self.reg_lambda = reg_lambda

        # ====================================================
        # RANDOM HIDDEN LAYER
        # ====================================================

        self.W = np.random.randn(
            input_size,
            hidden_size
        ) * 0.5

        self.b = np.random.randn(hidden_size) * 0.1

        # OUTPUT WEIGHTS
        self.beta = None

    # ========================================================
    # ACTIVATION FUNCTION
    # ========================================================

    def _activate(self, X):

        H = np.dot(X, self.W) + self.b

        if self.activation == 'relu':

            return np.maximum(0, H)

        elif self.activation == 'tanh':

            return np.tanh(H)

        elif self.activation == 'sigmoid':

            return 1 / (1 + np.exp(-H))

        else:

            raise ValueError("Unsupported activation")

    # ========================================================
    # TRAIN
    # ========================================================

    def fit(self, X, y):

        # Hidden layer matrix
        H = self._activate(X)

        # Regularization identity matrix
        I = np.identity(H.shape[1])

        # ====================================================
        # CLOSED FORM SOLUTION
        #
        # beta = (HᵀH + λI)^−1 Hᵀy
        # ====================================================

        self.beta = np.linalg.inv(
            H.T @ H + self.reg_lambda * I
        ) @ H.T @ y

    # ========================================================
    # PREDICT
    # ========================================================

    def predict(self, X):

        H = self._activate(X)

        return H @ self.beta


# ============================================================
# LOAD DATA
# ============================================================

print("\nLoading dataset...")

df = pd.read_csv(
    "/home/sanjeev/f110_ws/src/Data/data_files/method2V1V2_final_clean.csv"
)

print(f"✅ Dataset Loaded")
print(f"Samples: {len(df)}")

# ============================================================
# FEATURES
# ============================================================

X = df[[
    "d_m",
    "heading_error",
    "kappa",
    "vx",
    "kappa_lookahead"
]].values

# ============================================================
# TARGET
# ============================================================

y = df["steering"].values.reshape(-1, 1)

print(f"Feature shape : {X.shape}")
print(f"Target shape  : {y.shape}")

# ============================================================
# NORMALIZATION
# ============================================================

print("\nNormalizing features...")

scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)

# SAVE SCALER
joblib.dump(
    scaler,
    "elm_scaler.save"
)

print("✅ Scaler saved: elm_scaler.save")

# ============================================================
# TRAIN TEST SPLIT
# ============================================================

X_train, X_test, y_train, y_test = train_test_split(
    X_scaled,
    y,
    test_size=0.2,
    random_state=42,
    shuffle=True
)

print(f"\nTrain samples : {len(X_train)}")
print(f"Test samples  : {len(X_test)}")

# ============================================================
# HYPERPARAMETER TUNING
# ============================================================

print("\n" + "="*70)
print("HYPERPARAMETER TUNING")
print("="*70)

hidden_sizes = [32, 64, 128, 256]
reg_lambdas  = [1e-2, 1e-3, 1e-4]

results = []

best_rmse = float('inf')
best_model = None
best_params = None

for hidden_size in hidden_sizes:

    for reg_lambda in reg_lambdas:

        print(f"\nTesting:")
        print(f"Hidden Size : {hidden_size}")
        print(f"Lambda      : {reg_lambda}")

        # ====================================================
        # CREATE MODEL
        # ====================================================

        model = ELMRegressor(

            input_size=5,

            hidden_size=hidden_size,

            activation='relu',

            reg_lambda=reg_lambda
        )

        # ====================================================
        # TRAIN
        # ====================================================

        start_train = time.time()

        model.fit(X_train, y_train)

        train_time = time.time() - start_train

        # ====================================================
        # PREDICT
        # ====================================================

        start_inf = time.perf_counter()

        predictions = model.predict(X_test)

        end_inf = time.perf_counter()

        inference_time = (
            (end_inf - start_inf) / len(X_test)
        ) * 1000

        # ====================================================
        # METRICS
        # ====================================================

        mse = mean_squared_error(
            y_test,
            predictions
        )

        rmse = np.sqrt(mse)

        mae = mean_absolute_error(
            y_test,
            predictions
        )

        r2 = r2_score(
            y_test,
            predictions
        )

        print(f"RMSE : {rmse:.6f}")
        print(f"R2   : {r2:.6f}")

        # ====================================================
        # STORE RESULTS
        # ====================================================

        results.append({

            "hidden_size": hidden_size,

            "lambda": reg_lambda,

            "rmse": rmse,

            "mae": mae,

            "r2": r2,

            "train_time": train_time,

            "inference_time": inference_time
        })

        # ====================================================
        # SAVE BEST MODEL
        # ====================================================

        if rmse < best_rmse:

            best_rmse = rmse

            best_model = model

            best_params = {
                "hidden_size": hidden_size,
                "lambda": reg_lambda
            }

# ============================================================
# FINAL BEST MODEL RESULTS
# ============================================================

print("\n" + "="*70)
print("BEST ELM MODEL")
print("="*70)

print(f"Best Hidden Size : {best_params['hidden_size']}")
print(f"Best Lambda      : {best_params['lambda']}")
print(f"Best RMSE        : {best_rmse:.6f}")

# ============================================================
# SAVE BEST MODEL AS .PTH
# ============================================================

print("\nSaving best ELM model...")

torch.save(
    best_model,
    "model_elm.pth"
)

print("✅ Model saved as model_elm.pth")

# ============================================================
# SAVE METRICS TABLE
# ============================================================

results_df = pd.DataFrame(results)

results_df = results_df.sort_values(
    by="rmse"
)

results_df.to_csv(
    "elm_hyperparameter_results.csv",
    index=False
)

print("✅ Hyperparameter results saved")

# ============================================================
# FINAL EVALUATION USING BEST MODEL
# ============================================================

final_predictions = best_model.predict(X_test)

mse = mean_squared_error(
    y_test,
    final_predictions
)

rmse = np.sqrt(mse)

mae = mean_absolute_error(
    y_test,
    final_predictions
)

r2 = r2_score(
    y_test,
    final_predictions
)

print("\n" + "="*70)
print("FINAL EVALUATION")
print("="*70)

print(f"MSE  : {mse:.6f}")
print(f"RMSE : {rmse:.6f}")
print(f"MAE  : {mae:.6f}")
print(f"R2   : {r2:.6f}")

# ============================================================
# SAMPLE PREDICTIONS
# ============================================================

print("\nSample Predictions")

for i in range(10):

    print(
        f"Actual: {y_test[i][0]:.4f} | "
        f"Predicted: {final_predictions[i][0]:.4f}"
    )

# ============================================================
# PLOT 1 : RMSE COMPARISON
# ============================================================

plt.figure(figsize=(12, 6))

labels = []

rmses = []

for r in results:

    label = f"H={r['hidden_size']}\nλ={r['lambda']}"

    labels.append(label)

    rmses.append(r['rmse'])

bars = plt.bar(labels, rmses)

best_index = np.argmin(rmses)

bars[best_index].set_color('green')

plt.title(
    "ELM Hyperparameter Comparison",
    fontsize=14,
    fontweight='bold'
)

plt.ylabel("RMSE")

plt.xlabel("Configuration")

plt.grid(True, alpha=0.3)

# Add values on bars
for i, v in enumerate(rmses):

    plt.text(
        i,
        v + 0.0005,
        f"{v:.4f}",
        ha='center',
        fontsize=8
    )

plt.tight_layout()

plt.savefig(
    "elm_hyperparameter_comparison.png",
    dpi=150
)

print("\n✅ Saved: elm_hyperparameter_comparison.png")

# ============================================================
# PLOT 2 : ACTUAL VS PREDICTED
# ============================================================

plt.figure(figsize=(8, 8))

plt.scatter(
    y_test,
    final_predictions,
    alpha=0.4
)

min_val = min(y_test.min(), final_predictions.min())
max_val = max(y_test.max(), final_predictions.max())

plt.plot(
    [min_val, max_val],
    [min_val, max_val],
    'r--'
)

plt.title(
    "Actual vs Predicted Steering",
    fontsize=14,
    fontweight='bold'
)

plt.xlabel("Actual Steering")

plt.ylabel("Predicted Steering")

plt.grid(True, alpha=0.3)

plt.tight_layout()

plt.savefig(
    "elm_actual_vs_predicted.png",
    dpi=150
)

print("✅ Saved: elm_actual_vs_predicted.png")

# ============================================================
# PLOT 3 : PREDICTION ERROR DISTRIBUTION
# ============================================================

errors = y_test.flatten() - final_predictions.flatten()

plt.figure(figsize=(10, 5))

plt.hist(
    errors,
    bins=50
)

plt.title(
    "Prediction Error Distribution",
    fontsize=14,
    fontweight='bold'
)

plt.xlabel("Prediction Error")

plt.ylabel("Frequency")

plt.grid(True, alpha=0.3)

plt.tight_layout()

plt.savefig(
    "elm_error_distribution.png",
    dpi=150
)

print("✅ Saved: elm_error_distribution.png")

# ============================================================
# SUMMARY TABLE
# ============================================================

print("\n" + "="*70)
print("ALL HYPERPARAMETER RESULTS")
print("="*70)

print(results_df.to_string(index=False))

# ============================================================
# CONTROLLER INFO
# ============================================================

print("\n" + "="*70)
print("HOW TO USE IN ML CONTROLLER")
print("="*70)

print("""

1. MODEL PATH:
   elm_model_best.pth

2. SCALER PATH:
   elm_scaler.save

3. LOAD MODEL:

   import torch

   self.model = torch.load(
       "elm_model_best.pth"
   )

4. PREDICTION:

   steering = self.model.predict(features_scaled)[0][0]

""")

print("\n✅ ELM TRAINING COMPLETE")