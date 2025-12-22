//
// Created by kylec on 12/21/25.
//

#include <fstream>
#include "Lexer.h"

using namespace std;

void Lexer::init_keywords() {
    // TODO: aren't here like a billion keywords...
    keywords["int"] = TokenType::KEYWORD;
}

vector<string> Lexer::tokenize() {
    

}
