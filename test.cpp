//
// Created by kylec on 12/23/25.
//
#include <iostream>

using namespace std;

int add(int a, int b) {
    if (a > b) {
        return b;
    }

    cout << "TEST" << endl;

    if (b > a) {
        return a;
    }

    return a + b;
}