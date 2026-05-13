#include <stdio.h>
#include <stdlib.h>
#include <string.h>


__declspec(dllexport) double* load_csv_native(char* filename, int num_values) {
    
    
    double* memory = (double*)malloc(num_values * sizeof(double));
    if (memory == NULL) {
        printf("Error: Memory allocation failed!\n");
        return NULL;
    }
    

    FILE* file = fopen(filename, "r");
    if (file == NULL) {
        printf("Error: Could not open file %s\n", filename);
        return memory; // Return empty memory so it doesn't crash
    }

    // find out how big the file is
    fseek(file, 0, SEEK_END);
    long filesize = ftell(file);
    fseek(file, 0, SEEK_SET);

    //  Dump the file into RAM at once 
    char* buffer = (char*)malloc(filesize + 1);
    fread(buffer, 1, filesize, file);
    buffer[filesize] = '\0';
    fclose(file);

    // go through the RAM  and convert text to floats
    char* current_char = buffer;
    char* next_char;
    
   for (int i = 0; i < num_values; i++) {
        // strtod is the fastest way to extract a double from text
        memory[i] = strtod(current_char, &next_char);
        
        // skip the comma or any whitespace to get to the next number
        while (*next_char == ',' || *next_char == ' ' || *next_char == '\n' || *next_char == '\r') {
            next_char++;
        }
        current_char = next_char;
    }

    // clean the temporary text buffer
    free(buffer);
    
    return memory;
    }