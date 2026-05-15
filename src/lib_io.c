#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#if defined(_WIN32) || defined(__CYGWIN__)
#define LIBIO_API __declspec(dllexport)
#elif defined(__GNUC__) && __GNUC__ >= 4
#define LIBIO_API __attribute__((visibility("default")))
#else
#define LIBIO_API
#endif

LIBIO_API double* load_csv_native(char* filename, int num_values) {
    
    
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
    char* buffer = (char*)malloc((size_t)filesize + 1);
    if (buffer == NULL) {
        fclose(file);
        return memory;
    }
    if (fread(buffer, 1, (size_t)filesize, file) != (size_t)filesize) {
        free(buffer);
        fclose(file);
        return memory;
    }
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