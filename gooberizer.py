import sys
import subprocess
import clang.cindex

# needed to give clang include paths from g++
def get_system_include_paths():
    try:
        result = subprocess.run(
            ['g++', '-E', '-x', 'c++', '-', '-v'],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )

        paths = []
        is_include_section = False

        # Parse the output to find the lines following "#include <...> search starts here:"
        for line in result.stderr.splitlines():
            if "#include <...> search starts here:" in line:
                is_include_section = True
                continue
            if "End of search list." in line:
                is_include_section = False
                continue

            if is_include_section:
                # Clean up the path (remove leading spaces)
                path = line.strip()
                paths.append(f"-I{path}")

        return paths
    except FileNotFoundError:
        print("Error: 'gcc' command not found")
        return []

file_path = "test.cpp"
source_code = ""
include_paths = get_system_include_paths()

compiler_args = ['-std=c++17'] + include_paths

# get source code as a string
try:
    with open(file_path, 'r') as file:
        source_code = file.read()
except Exception as e:
    print(f"Error: {e}")

index = clang.cindex.Index.create()
tu = index.parse(file_path, args=compiler_args)

# print include info
for diag in tu.diagnostics:
    print(f"DIAGNOSTIC: {diag.spelling}")

# root node of AST
root = tu.cursor

def check_user_code(cursor):
    cursor_file = cursor.location.file.name
    if cursor_file == file_path:
        return True
    return False

def traverse_ast(cursor, indent=0):
    # skip this node if it's not in a file
    if cursor.location.file is None:
        for child in cursor.get_children():
            traverse_ast(child, indent + 1)
        return

    # only process the node if it's a user file
    if check_user_code(cursor):
        kind = cursor.kind.name
        name = cursor.spelling
        location = cursor.location

        print(f"{'  ' * indent}{kind}: '{name}' @ {str(location)}")

    for child in cursor.get_children():
        traverse_ast(child, indent + 1)

traverse_ast(root)

