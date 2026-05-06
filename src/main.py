import sys
from lexer import Lexer
from parser import Parser
from semantic import SemanticAnalyzer
from codegen import LLVMCodeGenerator
from visualizer import ASTPrinter # Ensure you have created visualizer.py!
from errors import CompilerError, LexerError, ParserError, SemanticError

def main():
    if len(sys.argv) < 2:
        print("Usage: python src/main.py <file.cstar>")
        sys.exit(1)

    file_path = sys.argv[1]
    
    try:
        with open(file_path, 'r') as file:
            source_code = file.read()
    except FileNotFoundError:
        print(f"Error: Could not find the file '{file_path}'")
        sys.exit(1)

    print(f"--- Compiling {file_path} ---")

    # Error Handling Wrapping

    # 1. Lexer
    print("1. Lexing...")
    try:
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()
    except LexerError as e:
        print(f"[Lexer Error] {e}")
        sys.exit(1)

    # 2. Parser
    print("2. Parsing...")
    try:
        parser = Parser(tokens)
        ast = parser.parse()
        print("AST Generated Successfully")

        print("\n--- ABSTRACT SYNTAX TREE (AST) ---")
        printer = ASTPrinter()
        printer.print_node(ast)
        print("----------------------------------\n")

    except ParserError as e:
        print(f"[Parser Error] {e}")
        sys.exit(1)

    # 3. Semantic Analysis
    print("3. Semantic Analysis...")
    try:
        analyzer = SemanticAnalyzer()
        analyzer.analyze(ast)
    except SemanticError as e:
        print(f"[Semantic Error] {e}")
        sys.exit(1)

    if analyzer.errors.has_errors():
        analyzer.errors.print_all()
        print("Compilation failed.")
        sys.exit(1)


    # 4. Code Generation
    print("4. Generating LLVM IR...")
    try:
        codegen = LLVMCodeGenerator()
        codegen.generate(ast)
    except CompilerError as e:
        print(f"[Codegen Error] {e}")
        sys.exit(1)

    print("4. Generating LLVM IR done.")

    # 5. Execution
    try:
        codegen.execute()
    except Exception as e:
        print(f"[Runtime Error] {e}")
        sys.exit(1)

    print("Success! (Pipeline is completely wired up)")