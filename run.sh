#!/usr/bin/env bash
set -euo pipefail

source_file="${1:-examples/hello.cast}"
compile_output="/tmp/castar_compile.out"
ir_file="/tmp/file.ll"
asm_file="/tmp/file.s"
bin_file="/tmp/file"

python3 src/main.py "$source_file" > "$compile_output"

awk '
    /^--- Generated LLVM IR ---$/ { in_ir = 1; next }
    /^--- End LLVM IR ---$/ { in_ir = 0; exit }
    in_ir { print }
' "$compile_output" > "$ir_file"

if [[ ! -s "$ir_file" ]]; then
    echo "Error: failed to extract LLVM IR from compiler output."
    exit 1
fi

llc "$ir_file" -o "$asm_file"
clang "$asm_file" -o "$bin_file" -no-pie
"$bin_file"
