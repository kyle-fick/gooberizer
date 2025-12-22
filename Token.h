//
// Created by kylec on 12/22/25.
//
#pragma once

enum class TokenType {
    KEYWORD,
    IDENTIFIER,
    INT_LITERAL,
    FLOAT_LITERAL,
    OPERATOR,
    PUNCTUATOR,
    UNKNOWN
};

struct Token {
    TokenType type;
    std::string lexeme;
    int index;
    int length;
};