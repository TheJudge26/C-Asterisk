import csv
import math
import time

# ─────────────────────────────────────────
#  CONFIG
# ─────────────────────────────────────────
DATA_PATH = "mnist_project/data/Mnist_Binary_0_vs_1_1000_20x20.csv"
W1_PATH   = "mnist_project/data/W1.csv"
B1_PATH   = "mnist_project/data/b1.csv"
W2_PATH   = "mnist_project/data/W2.csv"
B2_PATH   = "mnist_project/data/b2.csv"

NUM_SAMPLES = 1000
NUM_PIXELS  = 400
HIDDEN      = 64
EPOCHS      = 10
LR          = 0.01

total_start = time.time()

# ─────────────────────────────────────────
#  LOAD FLAT CSV
#  Same strategy as all other languages:
#  stream every value, skip header if present
# ─────────────────────────────────────────
def load_flat_csv(path, count, has_header=False):
    values = []
    with open(path, newline="") as f:
        reader = csv.reader(f)
        if has_header:
            next(reader)
        for row in reader:
            for val in row:
                val = val.strip()
                if val:
                    values.append(float(val))
                if len(values) >= count:
                    return values
    return values

print("Loading dataset and weights...")
load_start = time.time()

# flat: data[i*401 + p] = pixel p,  data[i*401 + 400] = label
data = load_flat_csv(DATA_PATH, NUM_SAMPLES * (NUM_PIXELS + 1), has_header=True)
W1   = load_flat_csv(W1_PATH, NUM_PIXELS * HIDDEN)
b1   = load_flat_csv(B1_PATH, HIDDEN)
W2   = load_flat_csv(W2_PATH, HIDDEN)
b2   = load_flat_csv(B2_PATH, 1)

load_time = time.time() - load_start
print(f"Loaded {NUM_SAMPLES} samples.")

# ─────────────────────────────────────────
#  ACTIVATIONS
# ─────────────────────────────────────────
def relu(x):       return x if x > 0.0 else 0.0
def relu_d(x):     return 1.0 if x > 0.0 else 0.0
def sigmoid(x):
    if x < -500:   return 0.0
    if x >  500:   return 1.0
    return 1.0 / (1.0 + math.exp(-x))

# Scratch buffers — same as C* z1_cache / a1_cache
z1_cache = [0.0] * HIDDEN
a1_cache = [0.0] * HIDDEN

# ─────────────────────────────────────────
#  TRAINING
# ─────────────────────────────────────────
print(f"\nTraining neural network: {NUM_PIXELS} -> {HIDDEN} -> 1")
print(f"Epochs: {EPOCHS}  |  LR: {LR}\n")
train_start = time.time()

for epoch in range(EPOCHS):
    for i in range(NUM_SAMPLES):
        base = i * (NUM_PIXELS + 1)

        # ── FORWARD PASS ──────────────────
        for h in range(HIDDEN):
            z = b1[h]
            for p in range(NUM_PIXELS):
                z += data[base + p] * W1[p * HIDDEN + h]
            z1_cache[h] = z
            a1_cache[h] = relu(z)

        z2    = b2[0]
        for h in range(HIDDEN):
            z2 += a1_cache[h] * W2[h]
        a2    = sigmoid(z2)
        label = data[base + NUM_PIXELS]
        d_a2  = a2 - label

        # ── BACKWARD PASS ─────────────────
        for h in range(HIDDEN):
            W2[h] -= LR * d_a2 * a1_cache[h]
        b2[0] -= LR * d_a2

        for h in range(HIDDEN):
            d_a1_h = d_a2 * W2[h] * relu_d(z1_cache[h])
            for p in range(NUM_PIXELS):
                W1[p * HIDDEN + h] -= LR * d_a1_h * data[base + p]
            b1[h] -= LR * d_a1_h

    print(f"  Epoch {epoch + 1}/{EPOCHS}")

train_time = time.time() - train_start

# ─────────────────────────────────────────
#  TESTING
# ─────────────────────────────────────────
print("\nTesting on all 1000 samples...")
test_start = time.time()

correct = 0
for i in range(NUM_SAMPLES):
    base = i * (NUM_PIXELS + 1)

    for h in range(HIDDEN):
        z = b1[h]
        for p in range(NUM_PIXELS):
            z += data[base + p] * W1[p * HIDDEN + h]
        a1_cache[h] = relu(z)

    z2 = b2[0]
    for h in range(HIDDEN):
        z2 += a1_cache[h] * W2[h]

    pred  = 1.0 if z2 > 0.0 else 0.0
    label = data[base + NUM_PIXELS]
    if pred == label:
        correct += 1

test_time  = time.time() - test_start
total_time = time.time() - total_start

# ─────────────────────────────────────────
#  RESULTS
# ─────────────────────────────────────────
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