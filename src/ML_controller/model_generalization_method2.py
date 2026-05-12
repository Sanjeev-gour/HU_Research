#!/usr/bin/env python3

import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib
import matplotlib.pyplot as plt

# =============================================================
# STEP 1: LOAD CLEANED MERGED DATASET
# Previously: single map data (training_data_overtake.csv)
# Now: all 4 maps x 2 velocity profiles = 79k clean samples
# =============================================================
df = pd.read_csv("merged_training_data_clean_final.csv")
print(f"✅ Loaded dataset | Rows: {len(df)}")

# =============================================================
# STEP 2: FEATURES AND LABELS
# Input  (X): 5 physics-based features (map-agnostic)
# Output (y): steering angle only
# =============================================================
X = df[["d_m", "heading_error", "kappa", "vx", "kappa_lookahead"]].values
y = df[["steering"]].values

print(f"   X shape : {X.shape}")
print(f"   y shape : {y.shape}")

# =============================================================
# STEP 3: NORMALIZATION
# StandardScaler: zero mean, unit variance
# Fit on ALL training data (not just one map like before)
# Scaler is saved and must be used in the controller too
# =============================================================
scaler = StandardScaler()
X = scaler.fit_transform(X)
joblib.dump(scaler, "scaler_generalized.save")
print(f"✅ Scaler fitted and saved as scaler_generalized.save")

# =============================================================
# STEP 4: TRAIN / VALIDATION SPLIT
# 80% training, 20% validation
# random_state=42 ensures reproducibility
# shuffle=True ensures map data is mixed (not sequential)
# =============================================================
X_train, X_val, y_train, y_val = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    shuffle=True
)

print(f"   Train samples : {len(X_train)}")
print(f"   Val samples   : {len(X_val)}")

# =============================================================
# STEP 5: CONVERT TO TENSORS
# =============================================================
X_train = torch.tensor(X_train, dtype=torch.float32)
y_train = torch.tensor(y_train, dtype=torch.float32)
X_val   = torch.tensor(X_val,   dtype=torch.float32)
y_val   = torch.tensor(y_val,   dtype=torch.float32)

# =============================================================
# STEP 6: MODEL DEFINITION
# Same architecture as before: 5 → 64 → 64 → 32 → 1
# Added Dropout(0.2) after first two layers
# Dropout randomly disables 20% of neurons during training
# This prevents overfitting to specific maps
# =============================================================
class SteeringModel(nn.Module):
    def __init__(self):
        super(SteeringModel, self).__init__()

        self.net = nn.Sequential(
            nn.Linear(5, 64),
            nn.ReLU(),
            nn.Dropout(0.2),          # drops 20% neurons → better generalization

            nn.Linear(64, 64),
            nn.ReLU(),
            nn.Dropout(0.2),          # drops 20% neurons → better generalization

            nn.Linear(64, 32),
            nn.ReLU(),

            nn.Linear(32, 1)          # output: single steering value
        )

    def forward(self, x):
        return self.net(x)

model = SteeringModel()

# Print model summary
total_params = sum(p.numel() for p in model.parameters())
print(f"\n✅ Model created | Total parameters: {total_params}")

# =============================================================
# STEP 7: LOSS, OPTIMIZER, SCHEDULER
# Loss     : MSELoss — standard for regression
# Optimizer: Adam lr=0.001
# Scheduler: ReduceLROnPlateau — reduces lr when val loss
#            stops improving, helps escape plateaus
# =============================================================
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Reduce LR by factor 0.5 if val loss doesn't improve for 100 epochs
scheduler = optim.lr_scheduler.ReduceLROnPlateau(
    optimizer,
    mode='min',
    patience=100,
    factor=0.5,
    verbose=True
)

# =============================================================
# STEP 8: EARLY STOPPING SETUP
# Stops training if val loss doesn't improve for 'patience' epochs
# Saves the best model automatically during training
# Prevents wasting time on epochs that no longer improve
# =============================================================
EARLY_STOP_PATIENCE = 200      # stop if no improvement for 200 epochs
best_val_loss       = float('inf')
epochs_no_improve   = 0
best_model_path     = "ml_model_generalized_best.pth"

# =============================================================
# STEP 9: TRAINING LOOP
# =============================================================
EPOCHS     = 2000
BATCH_SIZE = 256

train_loss_history = []   # for plotting
val_loss_history   = []   # for plotting

print(f"\n{'='*60}")
print(f"  Starting Training | Epochs: {EPOCHS} | Batch: {BATCH_SIZE}")
print(f"{'='*60}\n")

for epoch in range(EPOCHS):

    # ===== TRAIN =====
    model.train()
    perm       = torch.randperm(X_train.size(0))
    train_loss = 0.0

    for i in range(0, X_train.size(0), BATCH_SIZE):
        idx     = perm[i:i + BATCH_SIZE]
        batch_x = X_train[idx]
        batch_y = y_train[idx]

        optimizer.zero_grad()
        outputs = model(batch_x)
        loss    = criterion(outputs, batch_y)
        loss.backward()
        optimizer.step()

        train_loss += loss.item()

    # Normalize train loss by number of batches
    train_loss = train_loss / (X_train.size(0) // BATCH_SIZE)

    # ===== VALIDATION =====
    model.eval()
    with torch.no_grad():
        val_outputs = model(X_val)
        val_loss    = criterion(val_outputs, y_val).item()

    # ===== SCHEDULER STEP =====
    # Pass val_loss to scheduler — reduces LR if plateauing
    scheduler.step(val_loss)

    # ===== SAVE LOSS HISTORY =====
    train_loss_history.append(train_loss)
    val_loss_history.append(val_loss)

    # ===== EARLY STOPPING CHECK =====
    if val_loss < best_val_loss:
        best_val_loss     = val_loss
        epochs_no_improve = 0
        # Save best model whenever val loss improves
        torch.save(model.state_dict(), best_model_path)
    else:
        epochs_no_improve += 1

    if epochs_no_improve >= EARLY_STOP_PATIENCE:
        print(f"\n⚠️  Early stopping at epoch {epoch+1} | Best Val Loss: {best_val_loss:.6f}")
        break

    # ===== PRINT PROGRESS =====
    if (epoch + 1) == 1 or (epoch + 1) % 50 == 0 or (epoch + 1) == EPOCHS:
        print(f"Epoch {epoch+1:>4}/{EPOCHS} | "
              f"Train Loss: {train_loss:.6f} | "
              f"Val Loss: {val_loss:.6f} | "
              f"Best: {best_val_loss:.6f} | "
              f"LR: {optimizer.param_groups[0]['lr']:.6f}")

# =============================================================
# STEP 10: SAVE FINAL MODEL
# Two models saved:
# _best  → best validation loss during training (use this)
# _final → model state at last epoch
# =============================================================
torch.save(model.state_dict(), "ml_model_generalized_final.pth")

print(f"\n✅ Best model saved  : {best_model_path}")
print(f"✅ Final model saved : ml_model_generalized_final.pth")
print(f"✅ Best val loss     : {best_val_loss:.6f}")

# =============================================================
# STEP 11: PLOT TRAINING CURVES
# Shows train vs val loss over epochs
# Good training: both curves go down and stay close together
# Overfitting: val loss rises while train loss keeps dropping
# =============================================================
plt.figure(figsize=(12, 5))

plt.plot(train_loss_history, label='Train Loss', color='steelblue')
plt.plot(val_loss_history,   label='Val Loss',   color='orange')
plt.xlabel('Epoch')
plt.ylabel('MSE Loss')
plt.title('Training vs Validation Loss — Generalized Model')
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("training_curve_generalized.png")
plt.show()

print("✅ Training curve saved as training_curve_generalized.png")