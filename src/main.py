import sys
from lexer import Lexer
from parser import Parser
from semantic import SemanticAnalyzer
from codegen import LLVMCodeGenerator
from visualizer import ASTPrinter # Ensure you have created visualizer.py!

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

    # 1. Lexer
    print("1. Lexing...")
    lexer = Lexer(source_code)
    tokens = lexer.tokenize()

    # 2. Parser
    print("2. Parsing...")
    try:
        parser = Parser(tokens)
        ast = parser.parse()
        print("AST Generated Successfully")
        
        # --- NEW: AST Visualization ---
        # This will show you the "Skeleton" of your code in the terminal
        print("\n--- ABSTRACT SYNTAX TREE (AST) ---")
        printer = ASTPrinter()
        printer.print_node(ast)
        print("----------------------------------\n")
        
    except Exception as e:
        print(f"Parser Error: {e}")
        sys.exit(1)

    # 3. Semantic Analysis
    print("3. Semantic Analysis...")
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)

    # 4. LLVM Code Generation
    print("4. Generating LLVM IR...")
    codegen = LLVMCodeGenerator()
    codegen.generate(ast)
    
    # 5. Native Execution!
    codegen.execute()
    
    print("Success! (Pipeline is completely wired up)")

if __name__ == "__main__":
    main()