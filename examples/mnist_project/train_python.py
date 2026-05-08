import pandas as pd
import math
import time
import os

print("========================================")
print("     PURE PYTHON AI (Train & Predict)   ")
print("========================================\n")

# 1. Load the dataset
csv_path = os.path.join(os.path.dirname(__file__), "Mnist_Binary_0_vs_1_1000_20x20.csv")
df = pd.read_csv(csv_path)

# Split data: 100 for training, 10 completely new ones for testing!
train_df = df.head(100)
test_df = df.tail(10)

X_train, y_train = train_df.drop("label", axis=1).values, train_df["label"].values
X_test, y_test = test_df.drop("label", axis=1).values, test_df["label"].values

weights = [0.0] * 400
bias = 0.0
lr = 0.1

# --- PYTHON TRAINING ---
print("Training on 100 images...")
start_train = time.time()
for epoch in range(20):
    for i in range(100):
        sum_val = bias + sum(X_train[i][p] * weights[p] for p in range(400))
        pred = 1.0 / (1.0 + math.exp(-sum_val))
        err = y_train[i] - pred
        for p in range(400): weights[p] += lr * err * X_train[i][p]
        bias += lr * err
train_time = time.time() - start_train

# --- PYTHON PREDICTION ---
print("Predicting on 10 NEW images...")
start_pred = time.time()
correct = 0
for i in range(10):
    sum_val = bias + sum(X_test[i][p] * weights[p] for p in range(400))
    pred = 1.0 if sum_val > 0.0 else 0.0
    if pred == y_test[i]: correct += 1
pred_time = time.time() - start_pred

# --- RESULTS ---
print("\n--- PYTHON RESULTS ---")
print(f"Training Time:   {train_time:.6f} seconds")
print(f"Prediction Time: {pred_time:.6f} seconds")
print(f"Accuracy:        {correct}/10 correct")