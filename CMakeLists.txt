cmake_minimum_required(VERSION 4.0)
project(gooberizer)

set(CMAKE_CXX_STANDARD 20)

add_executable(gooberizer main.cpp
        Lexer.h
        Lexer.cpp)
