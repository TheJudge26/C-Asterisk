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

## ⚡ The MNIST Benchmark: ~20x Faster Than Pure Python

To prove C* isn't just theoretical, we implemented a **Single-Layer Perceptron** (a neural network) in pure C* and raced it against the mathematically identical implementation in pure Python. Both programs trained on 100 images from the MNIST handwritten digit dataset (binary classification: 0 vs. 1) and predicted on 10 unseen test images.

No NumPy. No PyTorch. No C++ libraries. Just raw math, compiled to native code.

| Language | Training Time | Accuracy |
|---|---|---|
| Pure Python | **0.860 seconds** | 10/10 |
| **C* (LLVM compiled)** | **0.045 seconds** | **10/10** |

**C* trained ~19× faster, with identical accuracy.**

The Python implementation uses standard `math.exp`, list comprehensions, and nested loops. The C* version — written in a language we built ourselves — compiles those same loops and arithmetic directly to x86-64 machine code through LLVM, achieving performance indistinguishable from hand-written C.

```cstar
# This is the actual C* code that beat Python by 19x.
class NativeAI {
    let weights: [float] = [0.0, 0.0, ...]  # 400 weights
    let bias: float = 0.0
    let lr: float = 0.1

    func train() -> float {
        for epoch in 20 {
            for i in 100 {
                let sum: float = self.bias
                for p in 400 {
                    let idx: int = (i * 400) + p
                    sum = sum + (self.train_img[idx] * self.weights[p])
                }
                let pred: float = 1.0 / (1.0 + exp(0.0 - sum))
                let err: float = self.train_lbl[i] - pred
                for p in 400 {
                    let idx: int = (i * 400) + p
                    self.weights[p] = self.weights[p] + (self.lr * err * self.train_img[idx])
                }
                self.bias = self.bias + (self.lr * err)
            }
        }
        return 1.0
    }
}
```

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

C* can call into native C shared libraries directly. The built-in `load_csv` function uses a compiled C extension (`lib_io.dll`) to stream large datasets into memory at full C speed — no Python I/O overhead.

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
- `llvmlite` (install via pip)
- A compiled `lib_io.dll` (or `.so` on Linux/macOS) in the `src/` directory for CSV support

```bash
pip install llvmlite
```

### Running a `.cstar` File

```bash
# Clone the repository
git clone https://github.com/your-username/cstar.git
cd cstar

# Compile and JIT-execute a .cstar program
python src/main.py examples/hello.cstar

# Compile the MNIST benchmark
python src/main.py examples/mnist_project/benchmark_fast.cstar

# To regenerate the MNIST data files first:
python examples/mnist_project/convert_data.py
python src/main.py examples/mnist_project/benchmark_fast.cstar
```

The compiler will print each phase as it runs, display the full AST, emit LLVM IR to stdout, JIT-execute the program, and save a native `.obj` file to the `obj/` directory.

```
--- Compiling examples/hello.cstar ---
1. Lexing...
2. Parsing...
AST Generated Successfully

--- ABSTRACT SYNTAX TREE (AST) ---
└── Program
    └── Print
        └── Value: StringNode (Hello, World!)
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
      │
      ▼
┌─────────────┐
│   LEXER     │  Breaks raw text into a flat stream of typed Tokens
└──────┬──────┘  (keywords, identifiers, operators, literals)
       │
       ▼
┌─────────────┐
│   PARSER    │  Consumes tokens via recursive descent and builds
└──────┬──────┘  an Abstract Syntax Tree (AST) of Python objects
       │
       ▼
┌──────────────────┐
│ SEMANTIC ANALYZER│  Walks the AST: resolves scopes, checks types,
└──────┬───────────┘  validates function signatures, reports errors
       │
       ▼
┌─────────────────┐
│  LLVM CODEGEN   │  Traverses the validated AST and emits
└──────┬──────────┘  LLVM Intermediate Representation (IR)
       │
       ▼
┌─────────────┐
│  LLVM       │  Applies optimization passes and compiles IR to
│  BACKEND    │  native x86-64 machine code ⚡
└─────────────┘
```

**The frontend (Lexer → Semantic Analyzer) is written entirely in Python** — fast to develop, readable, and easy to extend. **The backend is LLVM**, accessed through the `llvmlite` Python bindings. We hand LLVM our IR and it applies the same optimization passes used by Clang, Rust, and Swift, then emits machine code for the target architecture.

The division is intentional: we own the hard part (understanding C* syntax and semantics), and LLVM owns the other hard part (turning it into optimal machine code for every CPU on the planet).

---

## Project Structure

```
cstar/
├── src/
│   ├── main.py           ← Entry point — wires the full pipeline
│   ├── lexer.py          ← Tokenizer (hand-written, no regex)
│   ├── tokens.py         ← TokenType enum + Token class
│   ├── parser.py         ← Recursive descent parser + all AST nodes
│   ├── semantic.py       ← Type checker, scope resolution, symbol table
│   ├── codegen.py        ← LLVM IR generation via llvmlite
│   ├── visualizer.py     ← ASCII AST printer for debugging
│   ├── errors.py         ← Compiler error hierarchy
│   ├── error_list.py     ← Error accumulator
│   ├── lib_io.c          ← Native C extension for fast CSV loading
│   └── lib_io.dll        ← Compiled shared library (Windows)
│
├── examples/
│   └── mnist_project/
│       ├── benchmark_fast.cstar   ← The neural network in C*
│       ├── train_python.py        ← The identical Python benchmark
│       ├── convert_data.py        ← Prepares flat CSV data files
│       └── *.csv                  ← MNIST training/test data
│
├── obj/                  ← Compiled .obj files (generated at runtime)
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

Areas where contributions are especially welcome: a `string` type in codegen, `>=` / `<=` in codegen, a standard library, improved error messages with source highlighting, and Linux/macOS shared library support for `lib_io`.

---

## License

MIT © The C* Team. See [LICENSE](LICENSE) for details.

---

<div align="center">
  <sub>Built from scratch. Compiled to metal. Faster than Python.</sub>
</div>
