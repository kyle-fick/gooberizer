#include <iostream>
#include <string>
#include <vector>

using namespace std;

class goober_0 {
public:
    goober_0()
        : goober_1(false), goober_2("example"), goober_3(0) { }

    explicit goober_0(int goober_4);

    static int goober_5(int goober_6) {
        return goober_6 * 2;
    }

    int goober_7(int goober_8) {
        return goober_3 += goober_8;
    }

    void goober_9() {
        goober_10();
    }

private:
    void goober_10() {
        vector<double> goober_11(10, 1);
        for (int goober_12 = 0; goober_12 < goober_11.size(); ++goober_12) {
            goober_11[goober_12] *= goober_12;
        }

        for (double goober_13 : goober_11) {
            cout << goober_13 << '\n';
        }
    }

    bool goober_1;
    string goober_2;

    int goober_3;
};

goober_0::goober_0(int goober_15)
    : goober_1(true), goober_3(goober_15) { }

int main(int goober_16, char* goober_17[]) {
    goober_0 goober_18(10);
    goober_18.goober_7(100);
    goober_18.goober_9();
}