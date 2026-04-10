import sys
from lexer import Lexer
from parser import Parser
from semantic import SemanticAnalyzer
from codegen import LLVMCodeGenerator

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

    #Lexer
    print("1. Lexing...")
    lexer = Lexer(source_code)
    tokens = lexer.tokenize()

    for token in tokens:
        print(token)

    # parser
    print("2. Parsing...")
    try:
        parser = Parser(tokens)
        ast = parser.parse()
        print("AST Generated Successfully")
    except Exception as e:
        print(f"Parser Error: {e}")
    sys.exit(1)

    #Semantic Analysis
    print("3. Semantic Analysis...")
    analyzer = SemanticAnalyzer()
    analyzer.analyze(ast)

    #LLVM Code Generation
    print("4. Generating LLVM IR...")
    codegen = LLVMCodeGenerator()
    codegen.generate(ast)
    
    print("Success! (Pipeline is completely wired up)")

if __name__ == "__main__":
    main()