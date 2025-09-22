#!/usr/bin/env python3
"""
Clean training script - NO MLflow AT ALL
"""
import os
import sys
import json
import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
import torch.nn as nn
import numpy as np
from preprocess import load_and_preprocess

IS_CI = os.getenv('GITHUB_ACTIONS') == 'true'
print(f"Environment: {'GitHub Actions' if IS_CI else 'Local'}")

class BikeRentalModel(nn.Module):
    def __init__(self, input_size):  # FIXED: Double underscores
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_size, 64),
            nn.ReLU(),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
    
    def forward(self, x):
        return self.net(x)

def train_model():
    # Setup paths
    run_dir = Path("./runs") / datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    print("Loading data...")
    X_train, X_test, y_train, y_test = load_and_preprocess()
    
    X_train = X_train.astype(np.float32)
    y_train = y_train.astype(np.float32)
    X_test = X_test.astype(np.float32)
    y_test = y_test.astype(np.float32)
    
    # Model
    model = BikeRentalModel(X_train.shape[1])
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters())
    
    # Tensors
    X_train_t = torch.tensor(X_train)
    y_train_t = torch.tensor(y_train).reshape(-1, 1)
    X_test_t = torch.tensor(X_test)
    y_test_t = torch.tensor(y_test).reshape(-1, 1)
    
    # Train
    epochs = 10 if IS_CI else 100
    print(f"Training for {epochs} epochs...")
    
    for epoch in range(epochs):
        model.train()
        optimizer.zero_grad()
        loss = criterion(model(X_train_t), y_train_t)
        loss.backward()
        optimizer.step()
        
        if epoch % 10 == 0:
            print(f"Epoch {epoch}: Loss={loss.item():.4f}")
    
    # Save
    torch.save(model.state_dict(), run_dir / "model.pt")
    with open(run_dir / "metrics.json", 'w') as f:
        json.dump({"loss": float(loss.item())}, f)
    
    print(f"Done! Saved to {run_dir}")
    return True

if __name__ == "__main__":  # FIXED: Double underscores
    try:
        train_model()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
