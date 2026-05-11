import time
import math

print("--- Running Python Deep AI Benchmark ---")

# 1. The Data
inputs = [1.5, 2.0, -1.0]
weights = [0.5, -0.2, 0.1]
bias = 0.1

def forward():
    sum_val = bias
    for i in range(3):
        sum_val += inputs[i] * weights[i]
    
    # Sigmoid
    return 1.0 / (1.0 + math.exp(-sum_val))

start_time = time.time()

# Run the Neural Network 1 mil times
final_prediction = 0.0
for _ in range(1000000):
    final_prediction = forward()

end_time = time.time()

print(f"Prediction: {final_prediction:.6f}")
print(f"Python took: {end_time - start_time:.4f} seconds")