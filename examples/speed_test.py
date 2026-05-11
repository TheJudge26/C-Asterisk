import time

print("--- Running Python Benchmark ---")
start_time = time.time()

sum_val = 0.0
limit = 50000000

for i in range(limit):
    sum_val = sum_val + 1.0

end_time = time.time()

print(f"Result: {sum_val}")
print(f"Python took: {end_time - start_time:.4f} seconds")
