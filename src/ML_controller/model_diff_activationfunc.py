#!/usr/bin/env python3

import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib

# =============================================================
# STEP 1: LOAD DATA
# =============================================================
df = pd.read_csv("merged_training_data_clean_final.csv")
print(f"✅ Loaded | Rows: {len(df)}")

X = df[["d_m", "heading_error", "kappa", "vx", "kappa_lookahead"]].values
y = df[["steering"]].values

# =============================================================
# STEP 2: NORMALIZE
# One scaler for ALL models — activation function does not
# affect input scaling, only internal network computation
# Scaler is fitted on X (input features) only once
# =============================================================
scaler = StandardScaler()
X      = scaler.fit_transform(X)

# Save ONE scaler — same for all activation experiments
joblib.dump(scaler, "scaler_generalized.save")
print(f"✅ Scaler fitted and saved — same for all models")
print(f"   Mean : {scaler.mean_}")
print(f"   Std  : {scaler.scale_}")

# =============================================================
# STEP 3: TRAIN/VAL SPLIT
# Same split for ALL models — ensures fair comparison
# random_state=42 gives same split every time
# =============================================================
X_train, X_val, y_train, y_val = train_test_split(
    X, y, test_size=0.2, random_state=42, shuffle=True
)

X_train = torch.tensor(X_train, dtype=torch.float32)
y_train = torch.tensor(y_train, dtype=torch.float32)
X_val   = torch.tensor(X_val,   dtype=torch.float32)
y_val   = torch.tensor(y_val,   dtype=torch.float32)

print(f"   Train: {len(X_train)} | Val: {len(X_val)}")

# =============================================================
# STEP 4: BUILD MODEL
# Uses nn.Sequential directly — NO wrapper class
# This matches the controller which also uses nn.Sequential
# Keys will be: "0.weight", "3.weight" etc.
# =============================================================
def build_model(activation):
    """
    Builds model with given activation function
    Architecture: 5 → 64 → 64 → 32 → 1
    Uses nn.Sequential directly for compatibility
    with ML controller loading

    NOTE: SELU is self-normalizing → no Dropout needed
          All others use Dropout(0.1)

    Activation options:
      relu       → standard, fast
      leaky_relu → fixes dying neurons
      elu        → smooth negatives
      tanh       → zero centered
      selu       → self normalizing
    """
    acts = {
        'relu'       : nn.ReLU(),
        'leaky_relu' : nn.LeakyReLU(0.01),
        'elu'        : nn.ELU(alpha=1.0),
        'tanh'       : nn.Tanh(),
        'selu'       : nn.SELU()
    }
    act = acts[activation]

    # SELU works best without Dropout
    if activation == 'selu':
        model = nn.Sequential(
            nn.Linear(5, 64),
            act,
            nn.Linear(64, 64),
            act,
            nn.Linear(64, 32),
            act,
            nn.Linear(32, 1)
        )
    else:
        model = nn.Sequential(
            nn.Linear(5, 64),
            act,
            nn.Dropout(0.1),
            nn.Linear(64, 64),
            act,
            nn.Dropout(0.1),
            nn.Linear(64, 32),
            act,
            nn.Linear(32, 1)
        )
    return model

# =============================================================
# STEP 5: TRAINING FUNCTION
# Same hyperparameters for all — ensures fair comparison
# Three stopping conditions:
#   1. Early stopping   — no improvement for 300 epochs
#   2. Degradation stop — val loss rises 30% above best
#   3. Divergence stop  — val/train ratio exceeds 3x
# =============================================================
def train_model(model, activation_name):

    print(f"\n{'='*60}")
    print(f"  Training: {activation_name.upper()}")
    print(f"{'='*60}")

    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(),
                           lr=0.0005,
                           weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', patience=100, factor=0.5
    )

    EPOCHS                = 3000
    BATCH_SIZE            = 128
    EARLY_STOP_PATIENCE   = 300   # stop if no improvement
    DEGRADATION_THRESHOLD = 0.30  # stop if val rises 30% above best
    DIVERGENCE_THRESHOLD  = 3.0   # stop if val > 3x train

    best_val_loss     = float('inf')
    epochs_no_improve = 0
    best_epoch        = 0
    stop_reason       = "Max epochs reached"

    train_history = []
    val_history   = []

    for epoch in range(EPOCHS):

        # ── Train ──
        model.train()
        perm       = torch.randperm(X_train.size(0))
        train_loss = 0.0

        for i in range(0, X_train.size(0), BATCH_SIZE):
            idx     = perm[i:i+BATCH_SIZE]
            batch_x = X_train[idx]
            batch_y = y_train[idx]

            optimizer.zero_grad()
            outputs = model(batch_x)
            loss    = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()

        train_loss = train_loss / (X_train.size(0) // BATCH_SIZE)

        # ── Validate ──
        model.eval()
        with torch.no_grad():
            val_loss = criterion(model(X_val), y_val).item()

        scheduler.step(val_loss)
        train_history.append(train_loss)
        val_history.append(val_loss)

        # ── Save best model ──
        if val_loss < best_val_loss:
            best_val_loss     = val_loss
            epochs_no_improve = 0
            best_epoch        = epoch + 1
            # Save with weights_only compatible format
            torch.save(model.state_dict(),
                       f"ml_model_{activation_name}_best.pth")
        else:
            epochs_no_improve += 1

        # ==========================================================
        # STOPPING CONDITION 1: Early Stopping
        # Val loss not improving for EARLY_STOP_PATIENCE epochs
        # ==========================================================
        if epochs_no_improve >= EARLY_STOP_PATIENCE:
            stop_reason = f"Early stopping — no improvement for {EARLY_STOP_PATIENCE} epochs"
            print(f"\n  ⚠️  STOP: {stop_reason}")
            break

        # ==========================================================
        # STOPPING CONDITION 2: Degradation Stop
        # Val loss has risen 30% above best value
        # ==========================================================
        if val_loss > best_val_loss * (1 + DEGRADATION_THRESHOLD):
            stop_reason = (f"Degradation — val loss {val_loss:.6f} "
                           f"is {((val_loss/best_val_loss)-1)*100:.1f}% "
                           f"above best {best_val_loss:.6f}")
            print(f"\n  🔴 STOP: {stop_reason}")
            break

        # ==========================================================
        # STOPPING CONDITION 3: Divergence Stop
        # Val loss is 3x higher than train loss
        # Only checked after epoch 100 (early training is noisy)
        # ==========================================================
        if epoch > 100 and val_loss > train_loss * DIVERGENCE_THRESHOLD:
            stop_reason = (f"Divergence — val/train = "
                           f"{val_loss/train_loss:.2f}x "
                           f"exceeds {DIVERGENCE_THRESHOLD}x threshold")
            print(f"\n  🔴 STOP: {stop_reason}")
            break

        # ── Print progress ──
        if (epoch+1) == 1 or (epoch+1) % 100 == 0:
            ratio = val_loss / train_loss if train_loss > 0 else 0
            print(f"  Epoch {epoch+1:>4} | "
                  f"Train: {train_loss:.6f} | "
                  f"Val: {val_loss:.6f} | "
                  f"Best: {best_val_loss:.6f} | "
                  f"Ratio: {ratio:.2f}x | "
                  f"LR: {optimizer.param_groups[0]['lr']:.6f} | "
                  f"No-imp: {epochs_no_improve}/{EARLY_STOP_PATIENCE}")

    print(f"\n  ✅ Stop reason   : {stop_reason}")
    print(f"  ✅ Best Val Loss : {best_val_loss:.6f}")
    print(f"  ✅ Best Epoch    : {best_epoch}")
    print(f"  ✅ RMSE          : {np.sqrt(best_val_loss):.4f} rad")
    print(f"  ✅ Saved         : ml_model_{activation_name}_best.pth")

    return train_history, val_history, best_val_loss, best_epoch, stop_reason

# =============================================================
# STEP 6: TRAIN ALL ACTIVATIONS
# =============================================================
activations = ['relu', 'leaky_relu', 'elu', 'tanh', 'selu']

results   = {}
histories = {}

for act in activations:
    model = build_model(act)
    train_h, val_h, best_loss, best_ep, stop_r = train_model(model, act)

    results[act]   = {
        'best_val_loss' : best_loss,
        'best_epoch'    : best_ep,
        'total_epochs'  : len(train_h),
        'stop_reason'   : stop_r,
        'rmse'          : np.sqrt(best_loss)
    }
    histories[act] = {'train': train_h, 'val': val_h}

# =============================================================
# STEP 7: COMPARISON TABLE
# =============================================================
best_activation = min(results, key=lambda x: results[x]['best_val_loss'])

print(f"\n{'='*80}")
print(f"  FINAL ACTIVATION FUNCTION COMPARISON")
print(f"{'='*80}")
print(f"{'Activation':<15} {'Val Loss':>10} {'RMSE':>10} "
      f"{'Best Ep':>10} {'Epochs':>8}  Stop Reason")
print(f"{'-'*80}")

for act, res in results.items():
    marker = "  ★ BEST" if act == best_activation else ""
    print(f"{act:<15} {res['best_val_loss']:>10.6f} "
          f"{res['rmse']:>10.4f} "
          f"{res['best_epoch']:>10} "
          f"{res['total_epochs']:>8}  "
          f"{res['stop_reason'][:35]}"
          f"{marker}")

print(f"\n  ★ Best activation : {best_activation.upper()}")
print(f"  ★ Best val loss   : {results[best_activation]['best_val_loss']:.6f}")
print(f"  ★ RMSE            : {results[best_activation]['rmse']:.4f} rad")
print(f"  ★ Model to use    : ml_model_{best_activation}_best.pth")
print(f"  ★ Scaler to use   : scaler_generalized.save (same for all)")

# =============================================================
# STEP 8: PLOT TRAINING CURVES
# =============================================================
colors = {
    'relu'       : '#2196F3',
    'leaky_relu' : '#FF5722',
    'elu'        : '#4CAF50',
    'tanh'       : '#9C27B0',
    'selu'       : '#FF9800'
}

fig, axes = plt.subplots(2, 3, figsize=(18, 10))
fig.suptitle('Activation Function Comparison — Training Curves',
             fontsize=14, fontweight='bold')
axes = axes.flatten()

for i, act in enumerate(activations):
    ax        = axes[i]
    train_h   = histories[act]['train']
    val_h     = histories[act]['val']
    best_loss = results[act]['best_val_loss']
    best_ep   = results[act]['best_epoch']

    ax.plot(train_h, color=colors[act],
            linewidth=2, label='Train Loss', alpha=0.9)
    ax.plot(val_h, color=colors[act],
            linewidth=2, linestyle='--',
            label='Val Loss', alpha=0.7)

    # Mark best epoch with red dot and line
    ax.axvline(x=best_ep-1, color='red',
               linewidth=1.5, linestyle=':')
    ax.scatter([best_ep-1], [best_loss],
               color='red', s=100, zorder=5,
               label=f'Best ep={best_ep}')

    # Shade overfitting region after best epoch
    if best_ep < len(train_h):
        ax.axvspan(best_ep, len(train_h),
                   alpha=0.07, color='red',
                   label='Overfit zone')

    title_color = 'green' if act == best_activation else 'black'
    ax.set_title(f'{act.upper()}\nBest Val: {best_loss:.6f}',
                 fontweight='bold', color=title_color)
    ax.set_xlabel('Epoch')
    ax.set_ylabel('MSE Loss')
    ax.legend(fontsize=7)
    ax.grid(True, alpha=0.3)

    # Stats box
    ax.text(0.98, 0.98,
            f"Best Loss : {best_loss:.6f}\n"
            f"Best Epoch: {best_ep}\n"
            f"RMSE      : {results[act]['rmse']:.4f} rad\n"
            f"Stop      : {results[act]['stop_reason'][:20]}",
            transform=ax.transAxes,
            fontsize=7.5, va='top', ha='right',
            bbox=dict(boxstyle='round', facecolor='lightyellow',
                      alpha=0.9))

# Bar chart comparison
ax_bar      = axes[5]
act_names   = [a.replace('_', '\n').upper() for a in activations]
best_losses = [results[a]['best_val_loss'] for a in activations]
bar_colors  = ['gold' if a == best_activation else colors[a]
               for a in activations]

bars = ax_bar.bar(act_names, best_losses,
                  color=bar_colors, edgecolor='black', alpha=0.85)

for bar, loss, act in zip(bars, best_losses, activations):
    ax_bar.text(bar.get_x() + bar.get_width()/2,
                bar.get_height() + max(best_losses)*0.003,
                f'{loss:.6f}', ha='center',
                va='bottom', fontsize=8)
    if act == best_activation:
        ax_bar.text(bar.get_x() + bar.get_width()/2,
                    bar.get_height()/2,
                    'BEST', ha='center', fontsize=10,
                    fontweight='bold', color='red')

ax_bar.set_title('Best Val Loss — All Activations\n(Lower is Better)',
                 fontweight='bold')
ax_bar.set_ylabel('Best Validation Loss (MSE)')
ax_bar.grid(True, alpha=0.3, axis='y')

plt.tight_layout()
plt.savefig("activation_comparison.png", dpi=150, bbox_inches='tight')
plt.show()
print("\n✅ Plot saved as activation_comparison.png")

# =============================================================
# STEP 9: HOW TO UPDATE ML CONTROLLER
# After running — update these two lines in ML_controller.py
# =============================================================
print(f"\n{'='*60}")
print(f"  HOW TO UPDATE YOUR ML CONTROLLER")
print(f"{'='*60}")
print(f"""
  In ML_controller.py make these changes:

  1. Change model definition to nn.Sequential:
  
     # Remove SteeringModel class entirely
     # Use this instead:
     
     act = nn.{best_activation.upper() if best_activation == 'relu' else best_activation.title()}()
     
     self.model = nn.Sequential(
         nn.Linear(5, 64),  act, nn.Dropout(0.1),
         nn.Linear(64, 64), act, nn.Dropout(0.1),
         nn.Linear(64, 32), act,
         nn.Linear(32, 1)
     )

  2. Change model path:
     model_path = "ml_model_{best_activation}_best.pth"

  3. Change load line:
     self.model.load_state_dict(
         torch.load(model_path, weights_only=True)
     )

  4. Scaler stays the same:
     scaler_path = "scaler_generalized.save"
     (one scaler works for all activation functions)
""")