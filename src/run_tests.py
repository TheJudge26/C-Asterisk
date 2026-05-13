import os
import subprocess
import sys


TEST_FILES = [
    "examples/compare.cstar",
    "examples/math_test.cstar",
    "examples/string.cstar",
    "examples/hello.cstar"
    "examples/new_syntax.cstar"
]

def run_tests():
    passed = 0
    failed = 0
    
    print("--- Running C* Test Suite ---\n")
    
    for file_path in TEST_FILES:
        print(f"Testing {file_path}...", end=" ")
        
        
        if not os.path.exists(file_path):
            print("SKIPPED (File not found)")
            continue
            
        
        result = subprocess.run([sys.executable, "src/main.py", file_path], capture_output=True, text=True)
       
        if result.returncode == 0:
            print(" PASS")
            passed += 1
        else:
            print("FAIL")
            failed += 1
            
            print(f"   [Error Output]:\n{result.stdout.strip()}")
            
    print("\n--- Test Summary ---")
    print(f"Total: {passed + failed} | Passed: {passed} | Failed: {failed}")
    
    if failed > 0:
        sys.exit(1)

if __name__ == "__main__":
    run_tests()