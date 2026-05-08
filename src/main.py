import sys
import os
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
        analyzer.errors.print_errors()
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

    
     #test too
    # 5. Execution and Compilation
    try:
        # --- NEW: Load the C Standard Library ---
        import llvmlite.binding as llvm
        
        
        # Point LLVM to your compiled C code
        dll_path = os.path.join(os.path.dirname(__file__), "lib_io.dll")
        llvm.load_library_permanently(dll_path)
        # ----------------------------------------

    
        # Run it in RAM (JIT)
        codegen.execute()
        
        # NEW: Save it to a dedicated 'obj' folder (AOT)
        

        
        
        # 1. Safely create the 'obj' folder if it doesn't exist yet
        os.makedirs("obj", exist_ok=True) 
        
        # 2. Extract the file name (e.g., 'speed_test' from 'examples/speed_test.cstar')
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        
        # 3. Route the output path into the folder
        obj_path = os.path.join("obj", f"{base_name}.obj")
        
        # 4. Save the file!
        codegen.save_object(obj_path)

    
        
    except Exception as e:
        print(f"[Runtime Error] {e}")
        sys.exit(1)

    print("Success! (Pipeline is completely wired up)")

# CRITICAL FIX: This tells Python to actually execute the main() function 
# when you run `python src/main.py` from the terminal.
if __name__ == "__main__":
    main()