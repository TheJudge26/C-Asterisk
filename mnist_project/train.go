package main

import (
	"bufio"
	"fmt"
	"math"
	"os"
	"strconv"
	"strings"
	"time"
)

func loadCSV(path string, size int) []float64 {
	data := make([]float64, 0, size)

	file, err := os.Open(path)
	if err != nil {
		fmt.Printf("Error: Could not open file %s\n", path)
		return data
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	scanner.Buffer(make([]byte, 1024*1024*64), 1024*1024*64) 

	for scanner.Scan() {
		line := scanner.Text()
		parts := strings.Split(line, ",")
		for _, part := range parts {
			part = strings.TrimSpace(part)
			if part == "" {
				continue
			}
			val, err := strconv.ParseFloat(part, 64)
			if err == nil {
				data = append(data, val)
			}
			if len(data) >= size {
				return data
			}
		}
	}

	return data
}

func main() {
	fmt.Println("====================================")
	fmt.Println("        GO NATIVE AI BENCHMARK      ")
	fmt.Println("====================================\n")

	start := time.Now()

	trainX := loadCSV("train_X.csv", 40000)
	trainY := loadCSV("train_y.csv", 100)

	weights := make([]float64, 400)
	bias := 0.0
	lr := 0.1

	for epoch := 0; epoch < 20; epoch++ {
		for i := 0; i < 100; i++ {
			sum := bias
			for p := 0; p < 400; p++ {
				sum += trainX[i*400+p] * weights[p]
			}
			pred := 1.0 / (1.0 + math.Exp(-sum))
			err := trainY[i] - pred

			for p := 0; p < 400; p++ {
				weights[p] += lr * err * trainX[i*400+p]
			}
			bias += lr * err
		}
	}

	trainTime := time.Since(start)

	testX := loadCSV("test_X.csv", 4000)
	testY := loadCSV("test_y.csv", 10)

	correct := 0
	for i := 0; i < 10; i++ {
		sum := bias
		for p := 0; p < 400; p++ {
			sum += testX[i*400+p] * weights[p]
		}
		pred := 0.0
		if sum > 0.0 {
			pred = 1.0
		}
		if pred == testY[i] {
			correct++
		}
	}

	fmt.Println("--- GO RESULTS ---")
	fmt.Printf("Training Time:   %f seconds\n", trainTime.Seconds())
	fmt.Printf("Accuracy:        %d/10 correct\n", correct)
}