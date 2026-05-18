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

const (
	numSamples = 1000
	numPixels  = 400
	hidden     = 64
	epochs     = 10
	lr         = 0.01
)

// ─────────────────────────────────────────
//  LOAD FLAT CSV
//  Same strategy as all other languages:
//  stream every value, skip header if present
// ─────────────────────────────────────────
func loadFlatCSV(path string, count int, hasHeader bool) []float64 {
	data := make([]float64, 0, count)

	file, err := os.Open(path)
	if err != nil {
		fmt.Printf("Error: Could not open %s\n", path)
		return data
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	scanner.Buffer(make([]byte, 1024*1024*64), 1024*1024*64)

	if hasHeader {
		scanner.Scan() // skip header row
	}

	for scanner.Scan() && len(data) < count {
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
			if len(data) >= count {
				return data
			}
		}
	}
	return data
}

// ─────────────────────────────────────────
//  ACTIVATIONS
// ─────────────────────────────────────────
func relu(x float64) float64      { if x > 0.0 { return x }; return 0.0 }
func reluD(x float64) float64     { if x > 0.0 { return 1.0 }; return 0.0 }
func sigmoid(x float64) float64   { return 1.0 / (1.0 + math.Exp(-x)) }

func main() {
	totalStart := time.Now()

	// ─────────────────────────────────────
	//  LOAD DATA AND WEIGHTS
	// ─────────────────────────────────────
	fmt.Println("Loading dataset and weights...")
	loadStart := time.Now()

	// flat: data[i*401 + p] = pixel p,  data[i*401 + 400] = label
	data := loadFlatCSV(
		"mnist_project/data/Mnist_Binary_0_vs_1_1000_20x20.csv",
		numSamples*(numPixels+1), true)

	W1 := loadFlatCSV("mnist_project/data/W1.csv", numPixels*hidden, false)
	b1 := loadFlatCSV("mnist_project/data/b1.csv", hidden, false)
	W2 := loadFlatCSV("mnist_project/data/W2.csv", hidden, false)
	b2 := loadFlatCSV("mnist_project/data/b2.csv", 1, false)

	loadTime := time.Since(loadStart)
	fmt.Printf("Loaded %d samples.\n", numSamples)

	// Scratch buffers
	z1Cache := make([]float64, hidden)
	a1Cache := make([]float64, hidden)

	// ─────────────────────────────────────
	//  TRAINING
	// ─────────────────────────────────────
	fmt.Printf("\nTraining neural network: %d -> %d -> 1\n", numPixels, hidden)
	fmt.Printf("Epochs: %d  |  LR: %.3f\n\n", epochs, lr)

	trainStart := time.Now()

	for epoch := 0; epoch < epochs; epoch++ {
		for i := 0; i < numSamples; i++ {
			base := i * (numPixels + 1)

			// ── FORWARD PASS ──────────────────
			for h := 0; h < hidden; h++ {
				z := b1[h]
				for p := 0; p < numPixels; p++ {
					z += data[base+p] * W1[p*hidden+h]
				}
				z1Cache[h] = z
				a1Cache[h] = relu(z)
			}

			z2    := b2[0]
			for h := 0; h < hidden; h++ {
				z2 += a1Cache[h] * W2[h]
			}
			a2    := sigmoid(z2)
			label := data[base+numPixels]
			dA2   := a2 - label

			// ── BACKWARD PASS ─────────────────
			for h := 0; h < hidden; h++ {
				W2[h] -= lr * dA2 * a1Cache[h]
			}
			b2[0] -= lr * dA2

			for h := 0; h < hidden; h++ {
				dA1h := dA2 * W2[h] * reluD(z1Cache[h])
				for p := 0; p < numPixels; p++ {
					W1[p*hidden+h] -= lr * dA1h * data[base+p]
				}
				b1[h] -= lr * dA1h
			}
		}
		fmt.Printf("  Epoch %d/%d\n", epoch+1, epochs)
	}

	trainTime := time.Since(trainStart)

	// ─────────────────────────────────────
	//  TESTING
	// ─────────────────────────────────────
	fmt.Printf("\nTesting on all %d samples...\n", numSamples)
	testStart := time.Now()

	correct := 0
	for i := 0; i < numSamples; i++ {
		base := i * (numPixels + 1)

		for h := 0; h < hidden; h++ {
			z := b1[h]
			for p := 0; p < numPixels; p++ {
				z += data[base+p] * W1[p*hidden+h]
			}
			a1Cache[h] = relu(z)
		}

		z2 := b2[0]
		for h := 0; h < hidden; h++ {
			z2 += a1Cache[h] * W2[h]
		}

		pred  := 0.0
		if z2 > 0.0 { pred = 1.0 }
		label := data[base+numPixels]
		if pred == label {
			correct++
		}
	}

	testTime  := time.Since(testStart)
	totalTime := time.Since(totalStart)

	// ─────────────────────────────────────
	//  RESULTS
	// ─────────────────────────────────────
	fmt.Println("\n========================================")
	fmt.Printf("  FINAL ACCURACY: %d / %d\n", correct, numSamples)
	fmt.Printf("  (%.2f%%)\n", 100.0*float64(correct)/float64(numSamples))
	fmt.Println("========================================")
	fmt.Println("\n--- TIMING BREAKDOWN ---")
	fmt.Printf("  Load time:     %f seconds\n", loadTime.Seconds())
	fmt.Printf("  Training time: %f seconds\n", trainTime.Seconds())
	fmt.Printf("  Test time:     %f seconds\n", testTime.Seconds())
	fmt.Printf("  TOTAL time:    %f seconds\n", totalTime.Seconds())
	fmt.Println("------------------------")
}