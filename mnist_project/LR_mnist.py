import csv
import math
import time

DATASET_PATH = "mnist_project/data/Mnist_Binary_0_vs_1_1000_20x20.csv"
NUM_SAMPLES  = 1000
NUM_PIXELS   = 400
EPOCHS       = 5
LR           = 0.1

total_start = time.time()

# ─────────────────────────────────────────
#  LOAD DATASET  (no pandas / numpy)
# ─────────────────────────────────────────
print("Loading dataset...")
load_start = time.time()
X = []   
y = []   

with open(DATASET_PATH, newline="") as f:
    reader = csv.reader(f)
    next(reader)                          
    for row in reader:
        X.append([float(v) for v in row[:NUM_PIXELS]])
        y.append(int(row[NUM_PIXELS]))    

load_time = time.time() - load_start
print(f"Loaded {len(X)} samples, {len(X[0])} pixels each.")

# ─────────────────────────────────────────
#  INITIALISE WEIGHTS
# ─────────────────────────────────────────
weights = [0.0] * NUM_PIXELS
bias    = 0.0

def sigmoid(x):
    
    if x < -500: return 0.0
    if x >  500: return 1.0
    return 1.0 / (1.0 + math.exp(-x))

# ─────────────────────────────────────────
#  TRAINING  — logistic regression, 5 epochs
# ─────────────────────────────────────────
print(f"\nTraining for {EPOCHS} epochs on {NUM_SAMPLES} samples...")
train_start = time.time()

for epoch in range(EPOCHS):
    total_loss = 0.0
    for i in range(NUM_SAMPLES):
        
        z    = bias + sum(X[i][p] * weights[p] for p in range(NUM_PIXELS))
        pred = sigmoid(z)
        err  = y[i] - pred

        p_clip      = max(min(pred, 1.0 - 1e-12), 1e-12)
        total_loss += -(y[i] * math.log(p_clip) + (1 - y[i]) * math.log(1 - p_clip))

        for p in range(NUM_PIXELS):
            weights[p] += LR * err * X[i][p]
        bias += LR * err

    avg_loss = total_loss / NUM_SAMPLES
    print(f"  Epoch {epoch + 1}/{EPOCHS}  |  avg loss: {avg_loss:.6f}")

train_time = time.time() - train_start
print(f"\nTraining time: {train_time:.6f} seconds")

# ─────────────────────────────────────────
#  TESTING  — classify all 1000 samples
# ─────────────────────────────────────────
print("\nTesting on all 1000 samples...")
test_start = time.time()

correct = 0
for i in range(NUM_SAMPLES):
    z    = bias + sum(X[i][p] * weights[p] for p in range(NUM_PIXELS))
    pred = 1 if z > 0.0 else 0      
    if pred == y[i]:
        correct += 1

test_time  = time.time() - test_start
total_time = time.time() - total_start

print(f"\n{'='*40}")
print(f"  FINAL ACCURACY: {correct} / {NUM_SAMPLES}")
print(f"  ({100.0 * correct / NUM_SAMPLES:.2f}%)")
print(f"{'='*40}")
print(f"\n--- TIMING BREAKDOWN ---")
print(f"  Load time:     {load_time:.6f} seconds")
print(f"  Training time: {train_time:.6f} seconds")
print(f"  Test time:     {test_time:.6f} seconds")
print(f"  TOTAL time:    {total_time:.6f} seconds")
print(f"------------------------")