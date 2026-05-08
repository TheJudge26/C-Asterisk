import pandas as pd
import os

print("--- Building Fast .cstar Benchmark ---")

# 1. Load Original Data
base_dir = os.path.dirname(__file__)
csv_path = os.path.join(base_dir, "Mnist_Binary_0_vs_1_1000_20x20.csv")
df = pd.read_csv(csv_path)

train_df = df.head(100)
test_df = df.tail(10)

# 2. Export Clean, Flat CSVs for the C-Library to read
with open(os.path.join(base_dir, "train_X.csv"), "w") as f:
    f.write(",".join(map(str, train_df.drop("label", axis=1).values.flatten())) + ",")
with open(os.path.join(base_dir, "train_y.csv"), "w") as f:
    f.write(",".join(map(str, train_df["label"].values)) + ",")
with open(os.path.join(base_dir, "test_X.csv"), "w") as f:
    f.write(",".join(map(str, test_df.drop("label", axis=1).values.flatten())) + ",")
with open(os.path.join(base_dir, "test_y.csv"), "w") as f:
    f.write(",".join(map(str, test_df["label"].values)) + ",")

# 3. Generate the lightweight .cstar file
weights_str = "[" + ", ".join(["0.0"] * 400) + "]"

cstar_code = f"""
class NativeAI {{
    # INSTANT LOAD USING YOUR C-LIBRARY!
    let train_img: [float] = load_csv("examples/mnist_project/train_X.csv", 40000)
    let train_lbl: [float] = load_csv("examples/mnist_project/train_y.csv", 100)
    
    let test_img: [float] = load_csv("examples/mnist_project/test_X.csv", 4000)
    let test_lbl: [float] = load_csv("examples/mnist_project/test_y.csv", 10)
    
    let weights: [float] = {weights_str}
    let bias: float = 0.0
    let lr: float = 0.1

    func train() -> float {{
        for epoch in 20 {{
            for i in 100 {{
                let sum: float = self.bias
                for p in 400 {{ 
                    # Convert 2D logic to a 1D flat index
                    let idx: int = (i * 400) + p
                    sum = sum + (self.train_img[idx] * self.weights[p]) 
                }}
                let pred: float = 1.0 / (1.0 + exp(0.0 - sum))
                let err: float = self.train_lbl[i] - pred
                
                for p in 400 {{ 
                    let idx: int = (i * 400) + p
                    self.weights[p] = self.weights[p] + (self.lr * err * self.train_img[idx]) 
                }}
                self.bias = self.bias + (self.lr * err)
            }}
        }}
        return 1.0
    }}

    func predict() -> int {{
        let correct: int = 0
        for i in 10 {{
            let sum: float = self.bias
            for p in 400 {{ 
                let idx: int = (i * 400) + p
                sum = sum + (self.test_img[idx] * self.weights[p]) 
            }}
            let pred: float = 0.0
            if sum > 0.0 {{ pred = 1.0 }}
            if pred == self.test_lbl[i] {{ correct = correct + 1 }}
        }}
        return correct
    }}
}}

print(9999.0) # Start Flag
let ai = NativeAI()
ai.train()
let accuracy: int = ai.predict()
print(accuracy) 
print(1111.0) # Finish Flag
"""

with open(os.path.join(base_dir, "benchmark_fast.cstar"), "w") as f:
    f.write(cstar_code)

print("Success! Created 'benchmark_fast.cstar' and pure data files.")