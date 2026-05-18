import sys
import os
import subprocess
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
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
        print("Usage: cstar <file.cstar>     (Run instantly via JIT)")
        print("       cstar -b <file.cstar>  (Build executable via AOT)")
        sys.exit(1)

    is_build_mode = False
    if sys.argv[1] == "-b":
        if len(sys.argv) < 3:
            print("Error: Missing file path after -b")
            sys.exit(1)
        is_build_mode = True
        file_path = sys.argv[2]
    else:
        file_path = sys.argv[1]
    
    try:
        with open(file_path, 'r') as file:
            source_code = file.read()
    except FileNotFoundError:
        print(f"Error: Could not find the file '{file_path}'")
        sys.exit(1)

    print(f"--- Compiling {file_path} ---")

    

    
    print("1. Lexing...")
    try:
        lexer = Lexer(source_code)
        tokens = lexer.tokenize()
    except LexerError as e:
        print(f"[Lexer Error] {e}")
        sys.exit(1)

    
    print("2. Parsing...")
    
    parser = Parser(tokens)
    ast = parser.parse()

    
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


    
    print("4. Generating LLVM IR...")
    try:
        codegen = LLVMCodeGenerator()
        codegen.generate(ast)
    except CompilerError as e:
        print(f"[Codegen Error] {e}")
        sys.exit(1)

    print("4. Generating LLVM IR done.")

    
    #test too
    
    try:
        _try_load_lib_io()

        if is_build_mode:
            
            os.makedirs("obj", exist_ok=True) 
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            obj_path = os.path.join("obj", f"{base_name}{_native_object_extension()}")
            
            
            codegen.save_object(obj_path)
            
        
            print("5. Linking executable...")
            exe_name = f"{base_name}.exe" if platform.system() == "Windows" else base_name
            exe_path = os.path.join("obj", exe_name)
            
            
            try:
                subprocess.run(["clang", obj_path, "-o", exe_path], check=True)
                print(f"\n✅ Build Success! Standalone executable created at: {exe_path}")
                print(f"You can now run it directly: .\\{exe_path}")
            except Exception as e:
                print(f"\n[Linker Error] Make sure you have a C compiler (clang or gcc) installed on your system.")
                print(f"Details: {e}")
                sys.exit(1)
                
        else:
            
            codegen.execute()

    except Exception as e:
        print(f"[Runtime Error] {e}")
        sys.exit(1)

    print("Success! (Pipeline is completely wired up)")

