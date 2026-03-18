import pandas as pd
import torch
import torch.nn as nn

data = pd.read_csv("training_data_1.csv")

X = torch.tensor(data[["x","y","yaw"]].values,dtype=torch.float32)
Y = torch.tensor(data[["steering","speed"]].values,dtype=torch.float32)

model = nn.Sequential(
    nn.Linear(3,64),
    nn.ReLU(),
    nn.Linear(64,64),
    nn.ReLU(),
    nn.Linear(64,2)
)

optimizer = torch.optim.Adam(model.parameters(),lr=0.001)
loss_fn = nn.MSELoss()

for epoch in range(500):

    pred = model(X)
    loss = loss_fn(pred,Y)

    optimizer.zero_grad()
    loss.backward()
    optimizer.step()

print("Model trained")

# SAVE THE MODEL
torch.save(model.state_dict(), "ml_model_1.pth")

print("Model saved as ml_model_1.pth")