import time
import math

print("--- Python Deep Network Benchmark ---")

# 1. The Data
inputs = [1.5, 2.0, -1.0]

# Hidden Layer (3 Neurons) -> Requires a 2D Matrix!
h_weights = [
    [0.5, -0.2, 0.1],
    [-0.5, 0.8, -0.3],
    [0.2, 0.2, 0.2]
]
h_biases = [0.1, -0.1, 0.0]

# Output Layer (1 Neuron)
o_weights = [0.5, -0.5, 0.8]
o_bias = 0.1

def forward():
    # --- HIDDEN LAYER ---
    h0_sum = h_biases[0]
    for i in range(3): h0_sum += inputs[i] * h_weights[0][i]
    h0 = 1.0 / (1.0 + math.exp(-h0_sum))

    h1_sum = h_biases[1]
    for i in range(3): h1_sum += inputs[i] * h_weights[1][i]
    h1 = 1.0 / (1.0 + math.exp(-h1_sum))

    h2_sum = h_biases[2]
    for i in range(3): h2_sum += inputs[i] * h_weights[2][i]
    h2 = 1.0 / (1.0 + math.exp(-h2_sum))

    # --- OUTPUT LAYER ---
    out_sum = o_bias + (h0 * o_weights[0]) + (h1 * o_weights[1]) + (h2 * o_weights[2])
    return 1.0 / (1.0 + math.exp(-out_sum))

start_time = time.time()

# Run the Deep Network 1,000,000 times!
final_prediction = 0.0
for _ in range(1000000):
    final_prediction = forward()

end_time = time.time()

print(f"Prediction: {final_prediction:.6f}")
print(f"Python took: {end_time - start_time:.4f} seconds")