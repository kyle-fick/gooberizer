#include <iostream>
#include <string>
#include <vector>

using namespace std;

class Example {
public:
    Example()
        : boolean_member(false), string_member("example"), accumulator(0) { }

    explicit Example(int x);

    static int double_num(int a) {
        return a * 2;
    }

    int add(int x) {
        return accumulator += x;
    }

    void call_something() {
        do_something();
    }

private:
    void do_something() {
        vector<double> vec(10, 1);
        for (int i = 0; i < vec.size(); ++i) {
            vec[i] *= i;
        }

        for (double val : vec) {
            cout << val << '\n';
        }
    }

    bool boolean_member;
    string string_member;

    int accumulator;
};

Example::Example(int x)
    : boolean_member(true), accumulator(x) { }

int main(int argc, char* argv[]) {
    Example e(10);
    e.add(100);
    e.call_something();
}