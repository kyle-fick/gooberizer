# Gooberizer
A much-requested tool that takes your C++ source code and "gooberizes" it, turning most 
function, variable, enum, declarations, etc into `goober_n`. Gooberizer should work with
most, if not all C++ language features, including macros. Unfortunately, it's likely there
are still edge cases that will expose issues with the replacement algorithm, especially
with macros.

_**Note:**_ if you'd like to gooberize multiplle files in a project that reference each other,
you should pass them all to the program at once, otherwise it may rename the same reference
in different ways and lead to code that doesn't compile. 

## usage
To gooberize, you'll need python 3.7 or later (I think). The only library required is `libclang`,
which is used for C++ source code analysis and is what makes this project possible at all.
Using the script then requres that you first `pip install libclang`. After that, you should
be able to just use the script normally. Run the script with:

`python gooberizer.py [files] (args)`

## arguments
- `[files]`: List of files to gooberize, supports globbing expressions like `*.cpp`
- `-o, --output`: Specifies output directory to store gooberized files in, by default this is `gooberized`
- `-v, --verbose`: Verbose logging mode

## examples
Below is some example C++ code that demonstrates the gooberization process.
```` c++
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
````

After running `python gooberizer.py examples/example1.cpp`, we get:

````c++
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
````

This compiles and gives the same result as the original program! If we run the same command
with the verbose option `-v`, we get the full clang AST output of the user's code and the
replacement list for each file:

````
Getting system include paths...Done
First pass:
Processing example1.cpp...    NAMESPACE_REF: 'std' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 5, column 17>
  CLASS_DECL: 'Example' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 7, column 7>
    CONSTRUCTOR: 'Example' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 9, column 5>
      MEMBER_REF: 'boolean_member' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 10, column 11>
      MEMBER_REF: 'string_member' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 10, column 34>
        CALL_EXPR: 'basic_string' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 10, column 34>
            STRING_LITERAL: '"example"' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 10, column 48>
      MEMBER_REF: 'accumulator' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 10, column 60>
    CONSTRUCTOR: 'Example' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 12, column 14>
      PARM_DECL: 'x' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 12, column 26>
    CXX_METHOD: 'double_num' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 14, column 16>
      PARM_DECL: 'a' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 14, column 31>
            UNEXPOSED_EXPR: 'a' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 15, column 16>
              DECL_REF_EXPR: 'a' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 15, column 16>
    CXX_METHOD: 'add' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 18, column 9>
      PARM_DECL: 'x' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 18, column 17>
              MEMBER_REF_EXPR: 'accumulator' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 19, column 16>
              UNEXPOSED_EXPR: 'x' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 19, column 31>
                DECL_REF_EXPR: 'x' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 19, column 31>
    CXX_METHOD: 'call_something' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 22, column 10>
        CALL_EXPR: 'do_something' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 23, column 9>
          MEMBER_REF_EXPR: 'do_something' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 23, column 9>
    CXX_METHOD: 'do_something' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 27, column 10>
          VAR_DECL: 'vec' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 28, column 24>
            TEMPLATE_REF: 'vector' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 28, column 9>
              CALL_EXPR: 'vector' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 28, column 24>
            VAR_DECL: 'i' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 29, column 18>
            UNEXPOSED_EXPR: 'i' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 29, column 25>
              UNEXPOSED_EXPR: 'i' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 29, column 25>
                DECL_REF_EXPR: 'i' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 29, column 25>
            CALL_EXPR: 'size' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 29, column 29>
              MEMBER_REF_EXPR: 'size' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 29, column 33>
                UNEXPOSED_EXPR: 'vec' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 29, column 29>
                  DECL_REF_EXPR: 'vec' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 29, column 29>
            DECL_REF_EXPR: 'i' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 29, column 43>
                DECL_REF_EXPR: 'vec' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 30, column 13>
                UNEXPOSED_EXPR: 'i' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 30, column 17>
                  UNEXPOSED_EXPR: 'i' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 30, column 17>
                    DECL_REF_EXPR: 'i' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 30, column 17>
              UNEXPOSED_EXPR: 'i' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 30, column 23>
                UNEXPOSED_EXPR: 'i' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 30, column 23>
                  DECL_REF_EXPR: 'i' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 30, column 23>
          VAR_DECL: 'val' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 33, column 21>
                UNEXPOSED_EXPR: '__begin1' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 33, column 25>
                  DECL_REF_EXPR: '__begin1' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 33, column 25>
          DECL_REF_EXPR: 'vec' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 33, column 27>
                DECL_REF_EXPR: 'cout' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 34, column 13>
                UNEXPOSED_EXPR: 'val' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 34, column 21>
                  DECL_REF_EXPR: 'val' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 34, column 21>
    FIELD_DECL: 'boolean_member' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 38, column 10>
    FIELD_DECL: 'string_member' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 39, column 12>
      TYPE_REF: 'std::string' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 39, column 5>
    FIELD_DECL: 'accumulator' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 41, column 9>
  CONSTRUCTOR: 'Example' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 44, column 10>
    TYPE_REF: 'class Example' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 44, column 1>
    PARM_DECL: 'x' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 44, column 22>
    MEMBER_REF: 'boolean_member' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 45, column 7>
    MEMBER_REF: 'accumulator' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 45, column 29>
    UNEXPOSED_EXPR: 'x' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 45, column 41>
      DECL_REF_EXPR: 'x' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 45, column 41>
    PARM_DECL: 'argc' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 47, column 14>
    PARM_DECL: 'argv' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 47, column 26>
        VAR_DECL: 'e' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 48, column 13>
          TYPE_REF: 'class Example' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 48, column 5>
          CALL_EXPR: 'Example' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 48, column 13>
      CALL_EXPR: 'add' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 49, column 5>
        MEMBER_REF_EXPR: 'add' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 49, column 7>
          DECL_REF_EXPR: 'e' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 49, column 5>
      CALL_EXPR: 'call_something' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 50, column 5>
        MEMBER_REF_EXPR: 'call_something' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 50, column 7>
          DECL_REF_EXPR: 'e' @ <SourceLocation file '.../gooberizer/examples/example1.cpp', line 50, column 5>
Done
Second pass:
Processing example1.cpp...Successfully gooberized example1.cpp as gooberized/example1.cpp
REPLACEMENTS - .../gooberizer/examples/example1.cpp
 line    cols              original                  goober       usr_string
------------------------------------------------------------------
48    5-12      Example                       goober_0            c:@S@Example
44    10-17     Example                       goober_0            c:@S@Example@F@Example#I#
44    1-8       Example                       goober_0            c:@S@Example
12    14-21     Example                       goober_0            c:@S@Example@F@Example#I#
9     5-12      Example                       goober_0            c:@S@Example@F@Example#
7     7-14      Example                       goober_0            c:@S@Example
15    16-17     a                             goober_6            c:example1.cpp@252@S@Example@F@double_num#I#S@a
14    31-32     a                             goober_6            c:example1.cpp@252@S@Example@F@double_num#I#S@a
45    29-40     accumulator                   goober_3            c:@S@Example@FI@accumulator
41    9-20      accumulator                   goober_3            c:@S@Example@FI@accumulator
19    16-27     accumulator                   goober_3            c:@S@Example@FI@accumulator
10    60-71     accumulator                   goober_3            c:@S@Example@FI@accumulator
49    5-8       add                           goober_7            c:@S@Example@F@add#I#
18    9-12      add                           goober_7            c:@S@Example@F@add#I#
47    14-18     argc                          goober_16           c:example1.cpp@804@F@main#I#**C#@argc
47    26-30     argv                          goober_17           c:example1.cpp@814@F@main#I#**C#@argv
45    7-21      boolean_member                goober_1            c:@S@Example@FI@boolean_member
38    10-24     boolean_member                goober_1            c:@S@Example@FI@boolean_member
10    11-25     boolean_member                goober_1            c:@S@Example@FI@boolean_member
50    5-19      call_something                goober_9            c:@S@Example@F@call_something#
22    10-24     call_something                goober_9            c:@S@Example@F@call_something#
27    10-22     do_something                  goober_10           c:@S@Example@F@do_something#
23    9-21      do_something                  goober_10           c:@S@Example@F@do_something#
14    16-26     double_num                    goober_5            c:@S@Example@F@double_num#I#S
50    5-6       e                             goober_18           c:example1.cpp@834@F@main#I#**C#@e
49    5-6       e                             goober_18           c:example1.cpp@834@F@main#I#**C#@e
48    13-14     e                             goober_18           c:example1.cpp@834@F@main#I#**C#@e
30    23-24     i                             goober_12           c:example1.cpp@493@S@Example@F@do_something#@i
30    17-18     i                             goober_12           c:example1.cpp@493@S@Example@F@do_something#@i
29    43-44     i                             goober_12           c:example1.cpp@493@S@Example@F@do_something#@i
29    25-26     i                             goober_12           c:example1.cpp@493@S@Example@F@do_something#@i
29    18-19     i                             goober_12           c:example1.cpp@493@S@Example@F@do_something#@i
39    12-25     string_member                 goober_2            c:@S@Example@FI@string_member
10    34-47     string_member                 goober_2            c:@S@Example@FI@string_member
34    21-24     val                           goober_13           c:example1.cpp@576@S@Example@F@do_something#@val
33    21-24     val                           goober_13           c:example1.cpp@576@S@Example@F@do_something#@val
33    27-30     vec                           goober_11           c:example1.cpp@453@S@Example@F@do_something#@vec
30    13-16     vec                           goober_11           c:example1.cpp@453@S@Example@F@do_something#@vec
29    29-32     vec                           goober_11           c:example1.cpp@453@S@Example@F@do_something#@vec
28    24-27     vec                           goober_11           c:example1.cpp@453@S@Example@F@do_something#@vec
45    41-42     x                             goober_15           c:example1.cpp@740@S@Example@F@Example#I#@x
44    22-23     x                             goober_15           c:example1.cpp@740@S@Example@F@Example#I#@x
19    31-32     x                             goober_8            c:example1.cpp@302@S@Example@F@add#I#@x
18    17-18     x                             goober_8            c:example1.cpp@302@S@Example@F@add#I#@x
12    26-27     x                             goober_4            c:example1.cpp@217@S@Example@F@Example#I#@x
````