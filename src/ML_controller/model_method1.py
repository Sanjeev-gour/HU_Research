import pandas as pd
import torch
import torch.nn as nn
from sklearn.model_selection import train_test_split

# ===== LOAD DATA =====
data = pd.read_csv("/home/sanjeev/f110_ws/src/Data/training_data_1.csv")

X = data[["x","y","yaw"]].values
Y = data[["steering","speed"]].values

X = torch.tensor(X, dtype=torch.float32)
Y = torch.tensor(Y, dtype=torch.float32)

# ===== TRAIN / VALIDATION SPLIT =====
X_train, X_val, Y_train, Y_val = train_test_split(X, Y, test_size=0.2)

# ===== MODEL =====
model = nn.Sequential(
    nn.Linear(3,64),
    nn.ReLU(),
    nn.Linear(64,64),
    nn.ReLU(),
    nn.Linear(64,2)
)

optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
loss_fn = nn.MSELoss()

epochs = 4000

# ===== TRAINING LOOP =====
for epoch in range(epochs):

    # ---- TRAIN ----
    model.train()
    pred = model(X_train)
    train_loss = loss_fn(pred, Y_train)

    optimizer.zero_grad()
    train_loss.backward()
    optimizer.step()

    # ---- VALIDATION ----
    model.eval()
    with torch.no_grad():
        val_pred = model(X_val)
        val_loss = loss_fn(val_pred, Y_val)

    # ---- PRINT ----
    if epoch % 50 == 0:
        print(f"Epoch {epoch}/{epochs} | Train Loss: {train_loss.item():.4f} | Val Loss: {val_loss.item():.4f}")

print("Model trained")

# ===== SAVE MODEL =====
torch.save(model.state_dict(), "ml_model_5.pth")

print("Model saved as ml_model_5.pth")