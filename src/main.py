import sys
import os
import platform
from lexer import Lexer
from parser import Parser
from semantic import SemanticAnalyzer
from codegen import LLVMCodeGenerator
from visualizer import ASTPrinter 
from errors import CompilerError, LexerError, ParserError, SemanticError


def _native_object_extension():
    return ".obj" if platform.system() == "Windows" else ".o"


def _lib_io_shared_library_path():
    """Path to the native CSV helper next to this file; name depends on OS."""
    base = os.path.dirname(os.path.abspath(__file__))
    system = platform.system()
    if system == "Windows":
        name = "lib_io.dll"
    elif system == "Darwin":
        name = "lib_io.dylib"
    else:
        name = "lib_io.so"
    return os.path.join(base, name)


def _try_load_lib_io():
    """Load lib_io for load_csv; warn if missing (programs without load_csv still run)."""
    import llvmlite.binding as llvm

    path = _lib_io_shared_library_path()
    if not os.path.isfile(path):
        print(
            "\n[Notice] Native lib_io not found (expected at "
            f"{path}). Programs using load_csv need it; build with "
            "`make -f Makefile.lib_io lib_io` from the project root.\n"
        )
        return
    llvm.load_library_permanently(path)


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
    try:
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()
    except LexerError as e:
        print(f"[Lexer Error] {e}")
        sys.exit(1)

    # 2. Parser
    print("2. Parsing...")
    
    parser = Parser(tokens)
    ast = parser.parse()

    # ERROR CHECK 
    if parser.errors:
        print("\n--- PARSER ERRORS ---")
        for err in parser.errors:
            print(err)
        print("-----------------------\n")
        print("Compilation failed.")
        sys.exit(1)

    print("AST Generated Successfully")

    print("\n--- ABSTRACT SYNTAX TREE (AST) ---")
    printer = ASTPrinter()
    printer.print_node(ast)
    print("----------------------------------\n")

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
        _try_load_lib_io()

        codegen.execute()
        

        # create the 'obj' folder 
        os.makedirs("obj", exist_ok=True) 
        
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        
        obj_path = os.path.join("obj", f"{base_name}{_native_object_extension()}")
        
        codegen.save_object(obj_path)

    
        
    except Exception as e:
        print(f"[Runtime Error] {e}")
        sys.exit(1)

    print("Success! (Pipeline is completely wired up)")

if __name__ == "__main__":
    main()

