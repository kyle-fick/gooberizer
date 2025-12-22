//
// Created by kylec on 12/21/25.
//

#pragma once
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>
#include "Token.h"

// Lexer for tokenizing cpp source code. Only works on a single file
class Lexer {
public:
    Lexer(const std::string &filename)
        : source(filename) { }

    std::vector<std::string> tokenize();

private:
    void init_keywords();


    std::vector<Token> tokens;
    std::unordered_map<std::string, TokenType> keywords;

    std::ifstream source; // source code file as a stream
};
