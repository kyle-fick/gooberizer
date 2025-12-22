#include <iostream>
#include "Lexer.h"

using namespace std;

int main(int argc, char* argv[]) {
    std::ios_base::sync_with_stdio(false);

    if (argc != 1) {
        cout << "Usage: gooberize [source_code]" << endl;
        return 0;
    }

    Lexer lexer(argv[1]);
    vector<Token> tokens = lexer.tokenize();
}