#include <stdio.h>
#include <stdlib.h>

// Windows requires this special tag to export the function to Python/LLVM
__declspec(dllexport) double* load_csv_native(char* filename, int num_values) {
    
    // 1. Ask the computer for enough RAM to hold all the numbers
    double* memory = (double*)malloc(num_values * sizeof(double));
    
    // 2. Open the file
    FILE* file = fopen(filename, "r");
    if (file == NULL) {
        printf("Error: Could not open file %s\n", filename);
        return memory; // Return empty memory so it doesn't crash
    }
    
    // 3. Read the numbers incredibly fast
    for(int i = 0; i < num_values; i++) {
        fscanf(file, "%lf,", &memory[i]);
    }
    
    fclose(file);
    return memory;
}