"""
main.py — C* compiler entry point.

Level 6 Updates:
1. Milestone 3: Added report_error() for "Caret" (^) Diagnostics.
2. Wrapped the pipeline in try/except blocks to catch and visualize errors.
3. Preserved your original 4-phase orchestration.
"""

import sys

from lexer      import Lexer, LexerError
from parser     import Parser, ParseError
from semantic   import SemanticAnalyzer, SemanticError
from codegen    import LLVMCodeGenerator, CodeGenError
from visualizer import ASTPrinter


def report_error(source: str, message: str, line: int, col: int):
    """Milestone 3: Professional diagnostic reporter."""
    code_lines = source.splitlines()
    # Ensure the line index is within bounds
    if 0 < line <= len(code_lines):
        error_line = code_lines[line - 1]
        print(f"\n❌ [C* COMPILER ERROR]")
        print(f"Line {line}, Column {col}: {message}")
        print(f"   |")
        print(f"   | {error_line}")
        print(f"   | {' ' * (col - 1)}^")
        print(f"   |")
    else:
        print(f"\n❌ [C* COMPILER ERROR] Line {line}, Column {col}: {message}")
    sys.exit(1)


def compile_and_run(source_path: str):
    with open(source_path, "r") as f:
        source = f.read()

    try:
        # ── Phase 1: Lex ────────────────────────────────────────────
        print("[1/4] Lexing …")
        lexer  = Lexer(source)
        tokens = lexer.tokenize()

        # ── Phase 2: Parse ──────────────────────────────────────────
        print("[2/4] Parsing …")
        parser = Parser(tokens)
        ast    = parser.parse()

        # Visualizing the structure
        print("\n─── AST ──────────────────────────────────────────────")
        ASTPrinter().print_node(ast)
        print("──────────────────────────────────────────────────────\n")

        # ── Phase 4: Semantic analysis ──────────────────────────────
        print("[3/4] Analysing …")
        SemanticAnalyzer().analyze(ast)

        # ── Phase 5: Code generation & JIT execution ─────────────── 
        print("[4/4] Generating LLVM IR & executing …\n")
        codegen = LLVMCodeGenerator()
        codegen.generate(ast)
        codegen.execute()

    except (LexerError, ParseError, SemanticError, CodeGenError) as e:
        # Extract location info if the error provides it
        # We assume our custom errors were updated to store .line and .column
        msg = str(e)
        # Check if the error string contains our manual line/col info
        # and parse it, or check for attributes
        if "Line" in msg and "Col" in msg:
            # Basic parsing if attributes aren't present
            try:
                parts = msg.split(":")
                loc_info = parts[0] # "Line X, Col Y"
                actual_msg = parts[1].strip()
                line = int(loc_info.split(",")[0].split()[1])
                col = int(loc_info.split(",")[1].split()[1])
                report_error(source, actual_msg, line, col)
            except:
                print(f"\n❌ Fatal Error: {msg}")
                sys.exit(1)
        else:
            print(f"\n❌ Fatal Error: {msg}")
            sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py <file.cstar>")
        sys.exit(1)
    compile_and_run(sys.argv[1])


if __name__ == "__main__":
    main()