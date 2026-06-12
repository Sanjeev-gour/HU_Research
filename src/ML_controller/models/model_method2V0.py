    #!/usr/bin/env python3

    import torch
    import torch.nn as nn
    import torch.optim as optim
    import pandas as pd
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler
    import joblib

    # ===== LOAD DATA =====
    df = pd.read_csv("training_data_overtake.csv")

    X = df[["d_m", "heading_error", "kappa", "vx", "kappa_lookahead"]].values
    y = df[["steering"]].values

    # ===== NORMALIZATION =====
    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    # Save scaler
    joblib.dump(scaler, "scaler.save")

    # ===== TRAIN TEST SPLIT =====
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # ===== CONVERT TO TENSORS =====
    X_train = torch.tensor(X_train, dtype=torch.float32)
    y_train = torch.tensor(y_train, dtype=torch.float32)

    X_val = torch.tensor(X_val, dtype=torch.float32)
    y_val = torch.tensor(y_val, dtype=torch.float32)

    # ===== MODEL =====
    class SteeringModel(nn.Module):
        def __init__(self):
            super(SteeringModel, self).__init__()

            self.net = nn.Sequential(
                nn.Linear(5, 64),
                nn.ReLU(),
                nn.Linear(64, 64),
                nn.ReLU(),
                nn.Linear(64, 32),
                nn.ReLU(),
                nn.Linear(32, 1)
            )

        def forward(self, x):
            return self.net(x)

    model = SteeringModel()

    # ===== LOSS + OPTIMIZER =====
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    # ===== TRAINING =====
    EPOCHS = 2000
    BATCH_SIZE = 256

    for epoch in range(EPOCHS):

        model.train()
        perm = torch.randperm(X_train.size(0))

        train_loss = 0

        # ===== TRAIN LOOP =====
        for i in range(0, X_train.size(0), BATCH_SIZE):
            idx = perm[i:i+BATCH_SIZE]

            batch_x = X_train[idx]
            batch_y = y_train[idx]

            optimizer.zero_grad()

            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)

            loss.backward()
            optimizer.step()

            train_loss += loss.item()

        # ===== VALIDATION (ONLY ONCE PER EPOCH) =====
        model.eval()
        with torch.no_grad():
            val_outputs = model(X_val)
            val_loss = criterion(val_outputs, y_val).item()

        # ===== PRINT LOGIC =====
        if (epoch + 1) == 1 or (epoch + 1) % 50 == 0 or (epoch + 1) == EPOCHS:
            print(f"Epoch {epoch+1}/{EPOCHS} | Train Loss: {train_loss:.6f} | Val Loss: {val_loss:.6f}")

    # ===== SAVE MODEL =====
    torch.save(model.state_dict(), "method2_modelV0.pth")

    print("✅ Model saved as method2_modelV0.pth")
    print("✅ Scaler saved as scaler.save")