<div align="center">
  <img width="212" height="233" alt="Screenshot 2026-05-09 002134" src="https://github.com/user-attachments/assets/36b62d75-f20e-4bb3-a31b-c5fc696df045" />


  # C* (C-Asterisk)

  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Python](https://img.shields.io/badge/Frontend-Python-blue.svg)](https://www.python.org/)
  [![LLVM](https://img.shields.io/badge/Backend-LLVM%20%2F%20llvmlite-red.svg)](https://llvmlite.readthedocs.io/)

  **The simplicity of Python. The speed of C++. The power of LLVM.**

</div>

---

## What Is C*?

C* (pronounced *"C-Star"*) is a compiled, statically-typed programming language built from the ground up. The goal is simple: **you should never have to choose between readable code and fast code.**

Python is approachable — but slow. C++ is fast — but notoriously painful to write. C* occupies the ground between them: a clean, Python-inspired syntax that compiles directly to native machine code through the LLVM compiler infrastructure. The result is code that reads like a scripting language and runs at the speed of a systems language.

C* is directly inspired by **Mojo** (developed by Chris Lattner, the original creator of LLVM and Swift), which proved this architecture works at a professional level. C* is an independent, open-source exploration of the same core thesis — built from scratch.

---

## The MNIST Benchmark Suite

To prove C* is not just theoretical, we ran a full benchmark suite against Python, C++, and Go on the MNIST handwritten digit dataset (binary classification: 0 vs. 1, 1000 samples, 20x20 images unrolled to 400 pixels).

Every benchmark was held to the same strict rules:

- Same dataset, same file paths, same weight initialization (loaded from the same CSV files)
- Same CSV loading strategy across all four languages — a flat value stream, header skipped explicitly
- Same math: identical forward pass, backward pass, and weight update formulas
- No external ML libraries — no NumPy, no PyTorch, no Eigen
- No compiler optimization flags — C++ compiled with plain `g++`, no `-O2` or `-O3`
- All timings measured from first instruction to last, including data loading

The benchmarks were run twice: once for **Logistic Regression** (a single-layer model) and once for a **2-Layer Neural Network** with a hidden layer of 64 neurons using ReLU activation and sigmoid output.

---

### Benchmark 1 — Logistic Regression

Architecture: Input (400 pixels) -> Output (1 neuron, Sigmoid)
Training: 5 epochs, 1000 samples, learning rate 0.1

| Language | Load Time | Training Time | Test Time | Total Time | Accuracy |
|---|---|---|---|---|---|
| Python | 0.186s | 0.614s | 0.040s | **0.841s** | 1000/1000 |
| C* (LLVM) | — | — | — | **0.023s** | 1000/1000 |

**C* is ~37x faster than Python on Logistic Regression.**

The Python implementation spends the majority of its time in the training loop — 5 x 1000 x 400 = 2 million multiply-accumulate operations interpreted one by one. C* compiles those exact same loops to native x86-64 machine code through LLVM and finishes the entire program before Python has completed loading the dataset.

```cstar
class MnistTrainer {
    let data:    [float] = load_csv("mnist_project/data/Mnist_Binary_0_vs_1_1000_20x20.csv", 401000)
    let weights: [float] = load_csv("mnist_project/data/weights.csv", 400)
    let bias: float = 0.0
    let lr:   float = 0.1

    func train() -> int {
        for epoch in 5 {
            for i in 1000 {
                let base: int = i * 401
                let z: float = self.bias
                for p in 400 {
                    let idx: int = base + p
                    z = z + (self.data[idx] * self.weights[p])
                }
                let neg_z: float = 0.0 - z
                let pred:  float = 1.0 / (1.0 + exp(neg_z))
                let label_idx: int = base + 400
                let err: float = self.data[label_idx] - pred
                for p in 400 {
                    let idx: int = base + p
                    self.weights[p] = self.weights[p] + (self.lr * err * self.data[idx])
                }
                self.bias = self.bias + (self.lr * err)
            }
        }
        return 1
    }
}
```

---

### Benchmark 2 — 2-Layer Neural Network

Architecture: Input (400) -> Hidden (64 neurons, ReLU) -> Output (1 neuron, Sigmoid)
Training: 10 epochs, 1000 samples, learning rate 0.01, Xavier weight initialization

This is a real neural network with a full forward pass and backpropagation. Each training step computes layer-1 activations, caches them, computes the output, then propagates the gradient back through both layers to update 25,664 weights. All four languages implement the identical algorithm — single forward pass with cached activations reused in backprop, no redundant computation.

| Language | Load Time | Training Time | Test Time | Total Time | Accuracy |
|---|---|---|---|---|---|
| Python | 0.179s | 88.683s | 2.547s | **91.419s** | 1000/1000 |
| Go | 0.072s | 0.917s | 0.043s | **1.061s** | 1000/1000 |
| C++ | ~0.000s | 0.877s | 0.036s | **0.916s** | 1000/1000 |
| C* (LLVM) | — | — | — | **0.944s** | 1000/1000 |

**C* is ~97x faster than Python, on par with C++, and faster than Go.**

The gap between C* and Python grows with the size of the problem. A neural network performs roughly 128x more floating point operations per epoch than logistic regression. Python's interpreter overhead compounds with every additional operation. C* compiles the same math to the same machine instructions a C++ compiler would produce — the difference between C* and C++ is within normal run-to-run variance and does not represent a meaningful performance gap.

```cstar
class NeuralNet {
    let data:     [float] = load_csv("mnist_project/data/Mnist_Binary_0_vs_1_1000_20x20.csv", 401000)
    let W1:       [float] = load_csv("mnist_project/data/W1.csv", 25600)
    let b1:       [float] = load_csv("mnist_project/data/b1.csv", 64)
    let W2:       [float] = load_csv("mnist_project/data/W2.csv", 64)
    let b2:       [float] = load_csv("mnist_project/data/b2.csv", 1)
    let z1_cache: [float] = load_csv("mnist_project/data/b1.csv", 64)
    let a1_cache: [float] = load_csv("mnist_project/data/b1.csv", 64)
    let lr: float = 0.01

    func forward_one(i: int) -> float {
        let base: int = i * 401
        for h in 64 {
            let z1_h: float = self.b1[h]
            for p in 400 {
                let w1_idx: int = (p * 64) + h
                let d_idx:  int = base + p
                z1_h = z1_h + (self.data[d_idx] * self.W1[w1_idx])
            }
            self.z1_cache[h] = z1_h
            let a1_h: float = 0.0
            if z1_h > 0.0 { a1_h = z1_h }
            self.a1_cache[h] = a1_h
        }
        let z2: float = self.b2[0]
        for h in 64 {
            z2 = z2 + (self.a1_cache[h] * self.W2[h])
        }
        let neg_z2: float = 0.0 - z2
        return 1.0 / (1.0 + exp(neg_z2))
    }
}
```

---

### Full Results Summary

| Experiment | Python | Go | C++ | C* | C* vs Python |
|---|---|---|---|---|---|
| Logistic Regression | 0.841s | — | — | 0.023s | **37x faster** |
| Neural Network | 91.419s | 1.061s | 0.916s | 0.944s | **97x faster** |

The speedup grows with the size of the problem. A language built from scratch, with a Python frontend and an LLVM backend, matches the performance of C++ on a real machine learning workload — with none of C++'s complexity.

---

## Language Features

C* has a growing, production-aimed feature set. Every feature listed below is fully implemented in the compiler pipeline today.

### Variables & Type Annotations

C* is statically typed. Variables are declared with `let`. Type annotations are optional when the type can be inferred, but always supported.

```cstar
let x: int = 42
let pi: float = 3.14159
let name: string = "C-Star"
let flag: bool = true
```

### Arithmetic & Comparison Operators

All standard arithmetic and comparison operators are supported for `int` and `float` types.

```cstar
let a: int = 10
let b: int = 3
let sum: int = a + b        # 13
let product: int = a * b    # 30
let ratio: float = 10.0 / 3.0

# Comparisons produce bool
let bigger: bool = a > b        # true
let equal: bool = a == b        # false
let not_equal: bool = a != b    # true
let lte: bool = b <= 5          # true
```

### Print

```cstar
print(42)
print(3.14)
print("Hello from C*!")
```

### If / Else

```cstar
let score: int = 87

if score > 90 {
    print("A grade")
} else {
    print("Not quite an A")
}
```

### While Loops

```cstar
let i: int = 0
while i < 5 {
    print(i)
    i = i + 1
}
```

### For Loops

C* supports range-based `for` loops over integer counts and arrays.

```cstar
# Loop over a fixed integer range
for i in 10 {
    print(i)
}

# Loop over an array
let scores: [int] = [95, 87, 73, 100]
for s in scores {
    print(s)
}
```

### Functions with Return Types

Functions are declared with `func`, take typed parameters, and declare their return type with `->`.

```cstar
func add(a: int, b: int) -> int {
    return a + b
}

func sigmoid(x: float) -> float {
    return 1.0 / (1.0 + exp(0.0 - x))
}

let result: int = add(3, 7)    # 10
```

### Arrays

C* supports typed array literals and index-based access.

```cstar
let weights: [float] = [0.1, 0.5, -0.3, 0.9]
let first: float = weights[0]    # 0.1
weights[2] = 0.77                # mutate in place
```

### Classes & Methods

C* supports class declarations with fields and methods. `self` is used for instance access.

```cstar
class Counter {
    let count: int = 0

    func increment() -> int {
        self.count = self.count + 1
        return self.count
    }

    func reset() -> int {
        self.count = 0
        return 0
    }
}

let c = Counter()
c.increment()
c.increment()
print(c.count)    # 2
```

### Built-in Math Functions

C* bridges directly to the C standard math library, making these functions available natively at zero overhead.

```cstar
let y: float = exp(2.0)         # e^2
let r: float = sqrt(144.0)      # 12.0
let l: float = log(2.718)       # ~1.0
let p: float = pow(2.0, 10.0)   # 1024.0
```

### Native CSV Loading (C FFI)

C* can call into native C shared libraries directly. The built-in `load_csv` function uses a compiled C extension (`lib_io.dll` on Windows, `lib_io.so` on Linux, `lib_io.dylib` on macOS) to stream large datasets into memory at full C speed — no Python I/O overhead.

```cstar
let data: [float] = load_csv("dataset/train_X.csv", 40000)
let labels: [float] = load_csv("dataset/train_y.csv", 100)
```

### Comments

```cstar
# This is a single-line comment
let x: int = 5  # inline comment
```

---

## How to Run It

### Prerequisites

- Python 3.9+
- `llvmlite` — `pip install llvmlite`
- Optional: if you use `load_csv`, place a built native library in `src/`:
  - **Linux / macOS:** `make -f Makefile.lib_io lib_io`
  - **Windows:** compile `src/lib_io.c` to `lib_io.dll` (MSVC or MinGW, `-shared`).

### Running a `.cstar` File

```bash
# Clone the repository
git clone https://github.com/your-username/cstar.git
cd cstar

# Compile and JIT-execute a .cstar program
python src/main.py examples/hello.cstar

# Run the logistic regression benchmark
python src/main.py mnist_project/LR_mnist.cstar

# Run the neural network benchmark
python src/main.py mnist_project/nn_mnist.cstar
```

The compiler prints each phase as it runs, displays the full AST, emits LLVM IR, JIT-executes the program, and saves a native object file to the `obj/` directory (`.obj` on Windows, `.o` on Linux and macOS).

```
--- Compiling examples/hello.cstar ---
1. Lexing...
2. Parsing...
AST Generated Successfully

--- ABSTRACT SYNTAX TREE (AST) ---
`-- Program
    `-- Print
        `-- Value: StringNode (Hello, World!)
----------------------------------

3. Semantic Analysis...
   -> Semantic analysis passed successfully
4. Generating LLVM IR...
; ModuleID = "cstar_module"
...
4. Generating LLVM IR done.
Success! (Pipeline is completely wired up)
```

---

## How It Works — The Compiler Pipeline

Every `.cstar` file travels through five phases in order. Each phase has one job.

```
C* Source Code
      |
      v
+-------------+
|   LEXER     |  Breaks raw text into a flat stream of typed Tokens
+------+------+  (keywords, identifiers, operators, literals)
       |
       v
+-------------+
|   PARSER    |  Consumes tokens via recursive descent and builds
+------+------+  an Abstract Syntax Tree (AST) of Python objects
       |
       v
+------------------+
| SEMANTIC ANALYZER|  Walks the AST: resolves scopes, checks types,
+------+-----------+  validates function signatures, reports errors
       |
       v
+-----------------+
|  LLVM CODEGEN   |  Traverses the validated AST and emits
+------+----------+  LLVM Intermediate Representation (IR)
       |
       v
+-------------+
|  LLVM       |  Applies optimization passes and compiles IR to
|  BACKEND    |  native x86-64 machine code
+-------------+
```

**The frontend (Lexer through Semantic Analyzer) is written entirely in Python** — fast to develop, readable, and easy to extend. **The backend is LLVM**, accessed through the `llvmlite` Python bindings. We hand LLVM our IR and it applies the same optimization passes used by Clang, Rust, and Swift, then emits machine code for the target architecture.

The division is intentional: we own the hard part (understanding C* syntax and semantics), and LLVM owns the other hard part (turning it into optimal machine code for every CPU on the planet).

---

## Project Structure

```
cstar/
├── src/
│   ├── main.py           <- Entry point — wires the full pipeline
│   ├── lexer.py          <- Tokenizer (hand-written, no regex)
│   ├── tokens.py         <- TokenType enum + Token class
│   ├── parser.py         <- Recursive descent parser + all AST nodes
│   ├── semantic.py       <- Type checker, scope resolution, symbol table
│   ├── codegen.py        <- LLVM IR generation via llvmlite
│   ├── visualizer.py     <- ASCII AST printer for debugging
│   ├── errors.py         <- Compiler error hierarchy
│   ├── error_list.py     <- Error accumulator
│   ├── lib_io.c          <- Native C extension for fast CSV loading
│   └── lib_io.{dll,so,dylib}  <- Built locally (see Makefile.lib_io)
│
├── mnist_project/
│   ├── data/             <- MNIST CSV files and weight initialization files
│   ├── LR_mnist.cstar    <- Logistic regression in C*
│   ├── LR_mnist.py       <- Logistic regression in Python
│   ├── nn_mnist.cstar    <- Neural network in C*
│   ├── nn_mnist.py       <- Neural network in Python
│   ├── nn_mnist.cpp      <- Neural network in C++
│   └── nn_mnist.go       <- Neural network in Go
│
├── examples/             <- Small example .cstar programs
├── obj/                  <- Compiled object files (generated at runtime)
├── Makefile.lib_io       <- Builds lib_io.so / lib_io.dylib (Unix)
├── COMPILER_ARCHITECTURE.md
└── README.md
```

---

## Origin & Contributing

C* started as a **college compiler construction project** — a practical exploration of the question: *how does a programming language actually work?* We built every phase from scratch: no parser generators, no ANTLR, no shortcuts. Every token, every AST node, every LLVM instruction was written by hand.

It grew into something we're genuinely proud of, so we're releasing it under the **MIT License** as an open-source project. Whether you're learning how compilers work, want to contribute a new language feature, or just want to see a working LLVM pipeline written in plain Python, you're welcome here.

**To contribute:**
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-language-feature`)
3. Make your changes and add tests
4. Open a pull request with a description of what you built

Areas where contributions are especially welcome: a standard library, improved error messages with source highlighting, and further native/FFI polish (e.g. packaging `lib_io` for more targets).

---

## License

MIT - The C* Team. See [LICENSE](LICENSE) for details.

---

<div align="center">
  <sub>Built from scratch. Compiled to metal. Faster than Python.</sub>
</div>
