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
        return memory; 
    }

    fseek(file, 0, SEEK_END);
    long filesize = ftell(file);
    fseek(file, 0, SEEK_SET);

   
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

    char* current_char = buffer;
    char* next_char;
    
   for (int i = 0; i < num_values; i++) {
        
        memory[i] = strtod(current_char, &next_char);
       
        while (*next_char == ',' || *next_char == ' ' || *next_char == '\n' || *next_char == '\r') {
            next_char++;
        }
        current_char = next_char;
    }

    free(buffer);
    
    return memory;
    }