#include <iostream>
#include <fstream>
#include <vector>
#include <cmath>
#include <chrono>
#include <string>
#include <sstream>

using namespace std;
using namespace std::chrono;

const int    NUM_SAMPLES = 1000;
const int    NUM_PIXELS  = 400;
const int    HIDDEN      = 64;
const int    EPOCHS      = 10;
const double LR          = 0.01;

// ─────────────────────────────────────────
//  LOAD FLAT CSV
//  Same strategy as all other languages:
//  stream every value, skip header if present
// ─────────────────────────────────────────
vector<double> load_flat_csv(const string& path, int count, bool has_header = false) {
    vector<double> data;
    data.reserve(count);

    ifstream file(path);
    if (!file.is_open()) {
        cerr << "Error: Could not open " << path << endl;
        return data;
    }

    string line;

    if (has_header) {
        getline(file, line);
    }

    while (getline(file, line) && (int)data.size() < count) {
        stringstream ss(line);
        string token;
        while (getline(ss, token, ',') && (int)data.size() < count) {
            if (!token.empty()) {
                try { data.push_back(stod(token)); }
                catch (...) {}
            }
        }
    }
    return data;
}

// ─────────────────────────────────────────
//  ACTIVATIONS
// ─────────────────────────────────────────
inline double relu(double x)       { return x > 0.0 ? x : 0.0; }
inline double relu_d(double x)     { return x > 0.0 ? 1.0 : 0.0; }
inline double sigmoid(double x)    { return 1.0 / (1.0 + exp(-x)); }

int main() {
    auto total_start = high_resolution_clock::now();

    // ─────────────────────────────────────
    //  LOAD DATA AND WEIGHTS
    // ─────────────────────────────────────
    cout << "Loading dataset and weights..." << endl;
    auto load_start = high_resolution_clock::now();

    
    vector<double> data = load_flat_csv(
        "mnist_project/data/Mnist_Binary_0_vs_1_1000_20x20.csv",
        NUM_SAMPLES * (NUM_PIXELS + 1), true);

    vector<double> W1 = load_flat_csv("mnist_project/data/W1.csv", NUM_PIXELS * HIDDEN);
    vector<double> b1 = load_flat_csv("mnist_project/data/b1.csv", HIDDEN);
    vector<double> W2 = load_flat_csv("mnist_project/data/W2.csv", HIDDEN);
    vector<double> b2 = load_flat_csv("mnist_project/data/b2.csv", 1);

    auto load_end = high_resolution_clock::now();
    double load_time = duration<double>(load_end - load_start).count();
    cout << "Loaded " << NUM_SAMPLES << " samples." << endl;

    vector<double> z1_cache(HIDDEN);
    vector<double> a1_cache(HIDDEN);

    // ─────────────────────────────────────
    //  TRAINING
    // ─────────────────────────────────────
    cout << "\nTraining neural network: " << NUM_PIXELS
         << " -> " << HIDDEN << " -> 1" << endl;
    cout << "Epochs: " << EPOCHS << "  |  LR: " << LR << "\n" << endl;

    auto train_start = high_resolution_clock::now();

    for (int epoch = 0; epoch < EPOCHS; epoch++) {
        for (int i = 0; i < NUM_SAMPLES; i++) {
            int base = i * (NUM_PIXELS + 1);

            // ── FORWARD PASS ──────────────────
            for (int h = 0; h < HIDDEN; h++) {
                double z = b1[h];
                for (int p = 0; p < NUM_PIXELS; p++)
                    z += data[base + p] * W1[p * HIDDEN + h];
                z1_cache[h] = z;
                a1_cache[h] = relu(z);
            }

            double z2 = b2[0];
            for (int h = 0; h < HIDDEN; h++)
                z2 += a1_cache[h] * W2[h];
            double a2    = sigmoid(z2);
            double label = data[base + NUM_PIXELS];
            double d_a2  = a2 - label;

            // ── BACKWARD PASS ─────────────────
            for (int h = 0; h < HIDDEN; h++)
                W2[h] -= LR * d_a2 * a1_cache[h];
            b2[0] -= LR * d_a2;

            for (int h = 0; h < HIDDEN; h++) {
                double d_a1_h = d_a2 * W2[h] * relu_d(z1_cache[h]);
                for (int p = 0; p < NUM_PIXELS; p++)
                    W1[p * HIDDEN + h] -= LR * d_a1_h * data[base + p];
                b1[h] -= LR * d_a1_h;
            }
        }
        cout << "  Epoch " << epoch + 1 << "/" << EPOCHS << endl;
    }

    auto train_end = high_resolution_clock::now();
    double train_time = duration<double>(train_end - train_start).count();

    // ─────────────────────────────────────
    //  TESTING
    // ─────────────────────────────────────
    cout << "\nTesting on all " << NUM_SAMPLES << " samples..." << endl;
    auto test_start = high_resolution_clock::now();

    int correct = 0;
    for (int i = 0; i < NUM_SAMPLES; i++) {
        int base = i * (NUM_PIXELS + 1);

        for (int h = 0; h < HIDDEN; h++) {
            double z = b1[h];
            for (int p = 0; p < NUM_PIXELS; p++)
                z += data[base + p] * W1[p * HIDDEN + h];
            a1_cache[h] = relu(z);
        }

        double z2 = b2[0];
        for (int h = 0; h < HIDDEN; h++) z2 += a1_cache[h] * W2[h];

        double pred  = z2 > 0.0 ? 1.0 : 0.0;
        double label = data[base + NUM_PIXELS];
        if (pred == label) correct++;
    }

    auto test_end  = high_resolution_clock::now();
    auto total_end = high_resolution_clock::now();
    double test_time  = duration<double>(test_end  - test_start).count();
    double total_time = duration<double>(total_end - total_start).count();

    // ─────────────────────────────────────
    //  RESULTS
    // ─────────────────────────────────────
    cout << "\n========================================" << endl;
    cout << "  FINAL ACCURACY: " << correct << " / " << NUM_SAMPLES << endl;
    cout << "  (" << (100.0 * correct / NUM_SAMPLES) << "%)" << endl;
    cout << "========================================" << endl;
    cout << "\n--- TIMING BREAKDOWN ---" << endl;
    cout << "  Load time:     " << load_time  << " seconds" << endl;
    cout << "  Training time: " << train_time << " seconds" << endl;
    cout << "  Test time:     " << test_time  << " seconds" << endl;
    cout << "  TOTAL time:    " << total_time << " seconds" << endl;
    cout << "------------------------" << endl;

    return 0;
}