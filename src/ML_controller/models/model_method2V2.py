#!/usr/bin/env python3
"""
model_method2V2.py  —  Our Method 2 V2 Training Script

Two modes (select with --mode):

  activation   (default)
      Trains the V2 architecture with all five activation functions on the
      full multi-map dataset (method2V1V2_traintest_porto.csv) and produces the
      activation comparison table + training-curve plot.
      Output: ml_model_<act>_best.pth  +  scaler_holdout_porto.save
             (relu model also saved as model_method2V2_holdout_porto.pth)

  leave_one_out
      Trains the V2 ReLU model once per held-out map using the corresponding
      leave-one-out split dataset (method2V1V2_traintest_<map>.csv).
      Output: model_method2V2_holdout_<map>.pth  +  scaler_holdout_<map>.save

Both modes share the same architecture and hyperparameters reported in the paper.

Usage:
    python3 model_method2V2.py                        # activation comparison
    python3 model_method2V2.py --mode leave_one_out   # leave-one-map-out
    python3 model_method2V2.py --mode leave_one_out --maps overtake hangar
"""

import sys
import argparse
import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import joblib

DATA_DIR    = "/home/sanjeev/f110_ws/src/Data/data_files"
MODELS_DIR  = "/home/sanjeev/f110_ws/src/ML_controller/models_path"
SCALER_DIR  = "/home/sanjeev/f110_ws/src/ML_controller"

# Hyperparameters as reported in paper
LR                    = 5e-4
WEIGHT_DECAY          = 1e-4
BATCH_SIZE            = 128
DROPOUT               = 0.1
EPOCHS                = 3000
EARLY_STOP_PATIENCE   = 300
DEGRADATION_THRESHOLD = 0.30
DIVERGENCE_THRESHOLD  = 3.0

HOLDOUT_MAPS = ["overtake", "porto", "berlin", "hangar", "f"]


def build_model(activation='relu'):
    """
    Builds the V2 nn.Sequential model.

    Architecture: 5 → 64 → 64 → 32 → 1
    Dropout(0.1) after each of the first two hidden layers (except SELU which
    is self-normalising and works best without Dropout).

    Activation options: relu, leaky_relu, elu, tanh, selu
    """
    acts = {
        'relu'       : nn.ReLU(),
        'leaky_relu' : nn.LeakyReLU(0.01),
        'elu'        : nn.ELU(alpha=1.0),
        'tanh'       : nn.Tanh(),
        'selu'       : nn.SELU(),
    }
    act = acts[activation]

    if activation == 'selu':
        return nn.Sequential(
            nn.Linear(5, 64), act,
            nn.Linear(64, 64), act,
            nn.Linear(64, 32), act,
            nn.Linear(32, 1)
        )
    return nn.Sequential(
        nn.Linear(5, 64),  act, nn.Dropout(DROPOUT),
        nn.Linear(64, 64), act, nn.Dropout(DROPOUT),
        nn.Linear(64, 32), act,
        nn.Linear(32, 1)
    )


def train_model(model, X_train, y_train, X_val, y_val, label=''):
    """
    Trains model with V2 hyperparameters and three stopping conditions:
      1. Early stopping   — no improvement for EARLY_STOP_PATIENCE epochs
      2. Degradation stop — val loss rises 30% above best
      3. Divergence stop  — val/train ratio exceeds 3x (checked after epoch 100)

    Returns: train_history, val_history, best_val_loss, best_epoch, stop_reason
    """
    print(f"\n{'='*60}\n  Training: {label}\n{'='*60}")

    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', patience=100, factor=0.5
    )

    best_val_loss     = float('inf')
    best_state        = None
    epochs_no_improve = 0
    best_epoch        = 0
    stop_reason       = "Max epochs reached"
    train_history, val_history = [], []

    for epoch in range(EPOCHS):
        model.train()
        perm       = torch.randperm(X_train.size(0))
        epoch_loss = 0.0
        for i in range(0, X_train.size(0), BATCH_SIZE):
            idx  = perm[i:i + BATCH_SIZE]
            xb, yb = X_train[idx], y_train[idx]
            optimizer.zero_grad()
            loss = criterion(model(xb), yb)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item() * len(idx)
        train_loss = epoch_loss / X_train.size(0)

        model.eval()
        with torch.no_grad():
            val_loss = criterion(model(X_val), y_val).item()

        scheduler.step(val_loss)
        train_history.append(train_loss)
        val_history.append(val_loss)

        if val_loss < best_val_loss:
            best_val_loss     = val_loss
            best_state        = {k: v.clone() for k, v in model.state_dict().items()}
            best_epoch        = epoch + 1
            epochs_no_improve = 0
        else:
            epochs_no_improve += 1

        if epochs_no_improve >= EARLY_STOP_PATIENCE:
            stop_reason = f"Early stopping — no improvement for {EARLY_STOP_PATIENCE} epochs"
            print(f"\n  STOP: {stop_reason}")
            break
        if val_loss > best_val_loss * (1 + DEGRADATION_THRESHOLD):
            stop_reason = (f"Degradation — val {val_loss:.6f} is "
                           f"{((val_loss/best_val_loss)-1)*100:.1f}% above best")
            print(f"\n  STOP: {stop_reason}")
            break
        if epoch > 100 and val_loss > train_loss * DIVERGENCE_THRESHOLD:
            stop_reason = (f"Divergence — val/train = {val_loss/train_loss:.2f}x "
                           f"exceeds {DIVERGENCE_THRESHOLD}x")
            print(f"\n  STOP: {stop_reason}")
            break

        if (epoch + 1) == 1 or (epoch + 1) % 100 == 0:
            ratio = val_loss / train_loss if train_loss > 0 else 0
            print(f"  Epoch {epoch+1:>4} | Train {train_loss:.6f} | "
                  f"Val {val_loss:.6f} | Best {best_val_loss:.6f} | "
                  f"Ratio {ratio:.2f}x | LR {optimizer.param_groups[0]['lr']:.6f}")

    model.load_state_dict(best_state)
    rmse = best_val_loss ** 0.5
    print(f"\n  Stop   : {stop_reason}")
    print(f"  Best epoch {best_epoch} | val MSE {best_val_loss:.6f} | RMSE {rmse:.4f} rad")

    return train_history, val_history, best_val_loss, best_epoch, stop_reason


def activation_comparison_mode():
    print("Loading full dataset:", f"{DATA_DIR}/method2V1V2_traintest_porto.csv")
    df = pd.read_csv(f"{DATA_DIR}/method2V1V2_traintest_porto.csv")
    print(f"Rows: {len(df)}")

    X = df[["d_m", "heading_error", "kappa", "vx", "kappa_lookahead"]].values
    y = df[["steering"]].values

    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    joblib.dump(scaler, f"{SCALER_DIR}/scaler_holdout_porto.save")
    print(f"Scaler saved -> {SCALER_DIR}/scaler_holdout_porto.save")
    print(f"  Mean : {scaler.mean_}\n  Std  : {scaler.scale_}")

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, shuffle=True
    )
    X_train = torch.tensor(X_train, dtype=torch.float32)
    y_train = torch.tensor(y_train, dtype=torch.float32)
    X_val   = torch.tensor(X_val,   dtype=torch.float32)
    y_val   = torch.tensor(y_val,   dtype=torch.float32)
    print(f"Train: {len(X_train)} | Val: {len(X_val)}")

    activations = ['relu', 'leaky_relu', 'elu', 'tanh', 'selu']
    results, histories = {}, {}

    for act in activations:
        model = build_model(act)
        train_h, val_h, best_loss, best_ep, stop_r = train_model(
            model, X_train, y_train, X_val, y_val, label=act.upper()
        )
        out_path = f"{MODELS_DIR}/ml_model_{act}_best.pth"
        torch.save(model.state_dict(), out_path)
        print(f"  Saved -> {out_path}")
        if act == 'relu':
            porto_path = f"{MODELS_DIR}/model_method2V2_holdout_porto.pth"
            torch.save(model.state_dict(), porto_path)
            print(f"  Saved -> {porto_path}  (Porto holdout model)")
        results[act]   = {'best_val_loss': best_loss, 'best_epoch': best_ep,
                          'total_epochs': len(train_h), 'stop_reason': stop_r,
                          'rmse': np.sqrt(best_loss)}
        histories[act] = {'train': train_h, 'val': val_h}

    best_act = min(results, key=lambda x: results[x]['best_val_loss'])
    print(f"\n{'='*80}\n  ACTIVATION COMPARISON\n{'='*80}")
    print(f"{'Activation':<15} {'Val Loss':>10} {'RMSE':>10} {'Best Ep':>10}  Stop Reason")
    print('-' * 80)
    for act, res in results.items():
        marker = "  BEST" if act == best_act else ""
        print(f"{act:<15} {res['best_val_loss']:>10.6f} {res['rmse']:>10.4f} "
              f"{res['best_epoch']:>10}  {res['stop_reason'][:35]}{marker}")
    print(f"\n  Best activation : {best_act.upper()}")
    print(f"  Best val loss   : {results[best_act]['best_val_loss']:.6f}")
    print(f"  RMSE            : {results[best_act]['rmse']:.4f} rad")
    print(f"  Model to use    : ml_model_{best_act}_best.pth")
    print(f"  Scaler to use   : scaler_holdout_porto.save")

    colors = {'relu': '#2196F3', 'leaky_relu': '#FF5722', 'elu': '#4CAF50',
              'tanh': '#9C27B0', 'selu': '#FF9800'}
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    fig.suptitle('Activation Function Comparison — Training Curves',
                 fontsize=14, fontweight='bold')
    axes = axes.flatten()

    for i, act in enumerate(activations):
        ax = axes[i]
        train_h   = histories[act]['train']
        val_h     = histories[act]['val']
        best_loss = results[act]['best_val_loss']
        best_ep   = results[act]['best_epoch']

        ax.plot(train_h, color=colors[act], lw=2, label='Train', alpha=0.9)
        ax.plot(val_h,   color=colors[act], lw=2, ls='--', label='Val', alpha=0.7)
        ax.axvline(x=best_ep - 1, color='red', lw=1.5, ls=':')
        ax.scatter([best_ep - 1], [best_loss], color='red', s=100, zorder=5,
                   label=f'Best ep={best_ep}')
        if best_ep < len(train_h):
            ax.axvspan(best_ep, len(train_h), alpha=0.07, color='red')
        title_color = 'green' if act == best_act else 'black'
        ax.set_title(f'{act.upper()}\nBest Val: {best_loss:.6f}',
                     fontweight='bold', color=title_color)
        ax.set_xlabel('Epoch')
        ax.set_ylabel('MSE Loss')
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3)
        ax.text(0.98, 0.98,
                f"Best Loss : {best_loss:.6f}\nBest Epoch: {best_ep}\n"
                f"RMSE      : {results[act]['rmse']:.4f} rad\n"
                f"Stop      : {results[act]['stop_reason'][:20]}",
                transform=ax.transAxes, fontsize=7.5, va='top', ha='right',
                bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))

    ax_bar      = axes[5]
    act_names   = [a.replace('_', '\n').upper() for a in activations]
    best_losses = [results[a]['best_val_loss'] for a in activations]
    bar_colors  = ['gold' if a == best_act else colors[a] for a in activations]
    bars = ax_bar.bar(act_names, best_losses, color=bar_colors,
                      edgecolor='black', alpha=0.85)
    for bar, loss, act in zip(bars, best_losses, activations):
        ax_bar.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + max(best_losses) * 0.003,
                    f'{loss:.6f}', ha='center', va='bottom', fontsize=8)
        if act == best_act:
            ax_bar.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() / 2, 'BEST',
                        ha='center', fontsize=10, fontweight='bold', color='red')
    ax_bar.set_title('Best Val Loss — All Activations\n(Lower is Better)',
                     fontweight='bold')
    ax_bar.set_ylabel('Best Validation Loss (MSE)')
    ax_bar.grid(True, alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig(f"{MODELS_DIR}/activation_comparison.png",
                dpi=150, bbox_inches='tight')
    plt.show()
    print("Plot saved.")


def leave_one_out_mode(maps=None):
    if maps is None:
        maps = HOLDOUT_MAPS

    results = []
    for holdout_map in maps:
        print(f"\n{'='*60}\n  Holdout map: {holdout_map}\n{'='*60}")

        csv_path = f"{DATA_DIR}/method2V1V2_traintest_{holdout_map}.csv"
        df = pd.read_csv(csv_path)
        print(f"Loaded {csv_path} | Rows: {len(df)}")

        X = df[["d_m", "heading_error", "kappa", "vx", "kappa_lookahead"]].values
        y = df[["steering"]].values

        scaler = StandardScaler()
        X = scaler.fit_transform(X)
        scaler_path = f"{SCALER_DIR}/scaler_holdout_{holdout_map}.save"
        joblib.dump(scaler, scaler_path)
        print(f"Scaler saved -> {scaler_path}")

        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=0.2, random_state=42, shuffle=True
        )
        X_train = torch.tensor(X_train, dtype=torch.float32)
        y_train = torch.tensor(y_train, dtype=torch.float32)
        X_val   = torch.tensor(X_val,   dtype=torch.float32)
        y_val   = torch.tensor(y_val,   dtype=torch.float32)
        print(f"Train: {len(X_train)} | Val: {len(X_val)}")

        model = build_model('relu')
        _, _, best_loss, best_ep, stop_r = train_model(
            model, X_train, y_train, X_val, y_val,
            label=f"leave-one-out ({holdout_map})"
        )

        model_path = f"{MODELS_DIR}/model_method2V2_holdout_{holdout_map}.pth"
        torch.save(model.state_dict(), model_path)
        print(f"Model saved -> {model_path}")

        results.append({
            'map': holdout_map, 'best_epoch': best_ep,
            'val_mse': best_loss, 'rmse': best_loss ** 0.5,
            'stop': stop_r,
        })

    print(f"\n{'='*60}\n  LEAVE-ONE-OUT SUMMARY\n{'='*60}")
    for r in results:
        print(f"  {r['map']:10s}  epoch={r['best_epoch']:4d}  "
              f"MSE={r['val_mse']:.6f}  RMSE={r['rmse']:.4f}  {r['stop']}")


def main():
    parser = argparse.ArgumentParser(description='Train Our Method 2 V2')
    parser.add_argument('--mode', choices=['activation', 'leave_one_out'],
                        default='activation',
                        help='activation: compare all activations on full dataset; '
                             'leave_one_out: train per-holdout-map models (ReLU)')
    parser.add_argument('--maps', nargs='+', default=None,
                        help='(leave_one_out only) subset of maps to train, '
                             'e.g. --maps overtake berlin')
    args = parser.parse_args()

    if args.mode == 'activation':
        activation_comparison_mode()
    else:
        leave_one_out_mode(maps=args.maps)


if __name__ == '__main__':
    main()
