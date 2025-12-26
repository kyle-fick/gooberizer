# Gooberizer
A much-requested tool that takes your C++ source code and "gooberizes" it, turning most 
function, variable, enum, declarations, etc into `goober_n`. Gooberizer should work with
most, if not all C++ language features, including macros. Unfortunately, it's likely there
are still edge cases that will expose issues with the replacement algorithm

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