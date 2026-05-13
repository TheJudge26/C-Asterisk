#include <iostream>
#include <vector>
#include <fstream>
#include <chrono>
#include <cmath>
#include <sstream>

using namespace std;
using namespace std::chrono;


vector<double> load_csv(string path, int size) {
    vector<double> data;
    ifstream file(path);
    string val;
    while (getline(file, val, ',')) {
        if (!val.empty()) data.push_back(stod(val));
        if (data.size() >= size) break;
    }
    return data;
}

int main() {
    auto start = high_resolution_clock::now();

    
    auto train_X = load_csv("train_X.csv", 40000);
    auto train_y = load_csv("train_y.csv", 100);
    
    vector<double> weights(400, 0.0);
    double bias = 0.0;
    double lr = 0.1;

    for (int epoch = 0; epoch < 20; epoch++) {
        for (int i = 0; i < 100; i++) {
            double sum = bias;
            for (int p = 0; p < 400; p++) {
                sum += train_X[i * 400 + p] * weights[p];
            }
            double pred = 1.0 / (1.0 + exp(-sum));
            double err = train_y[i] - pred;

            for (int p = 0; p < 400; p++) {
                weights[p] += lr * err * train_X[i * 400 + p];
            }
            bias += lr * err;
        }
    }

    auto end = high_resolution_clock::now();
    duration<double> time_span = duration_cast<duration<double>>(end - start);
    cout << "C++ Execution Time: " << time_span.count() << " seconds" << endl;
    return 0;
}