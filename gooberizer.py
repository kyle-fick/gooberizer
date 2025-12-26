import os, sys
import re
import shutil
import argparse
import glob
import subprocess
import clang.cindex

# TODO: macro ifdefs cause some code not to be read. Allow users to specify cpp args

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
        print("Error: 'g++' command not found")
        return []


class Gooberizer:
    def __init__(self, file_paths, include_paths, output_dir="gooberized", verbose=False):
        self.files = [os.path.abspath(f) for f in file_paths]
        self.include_paths = include_paths

        self.output_dir = output_dir
        self.verbose = verbose

        self.goober_map = {}
        self.goober_n = 0

        # create gooberized output directory and remove old files
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
        os.makedirs(self.output_dir)


    def log(self, message):
        if self.verbose:
            print(message)

    def run(self):
        # first pass for building goober map
        print("First pass:")
        for file_path in self.files:
            print(f"Processing {os.path.basename(file_path)}")
            self._process_file(file_path, first_pass=True)

        # second pass for building replacement list and making replacements
        print("Second pass:")
        for file_path in self.files:
            print(f"Processing {os.path.basename(file_path)}")
            self._process_file(file_path, first_pass=False)

            self._print_replacement_table(file_path)


    def _print_replacement_table(self, file_path):
        self.current_replacements.sort(key=lambda x: x['original'])
        self.log(f"REPLACEMENTS - {file_path}")
        self.log(f"{'line':^6}{'cols':^10}{'original':^30}{'goober':^20}{'usr_string'}")
        self.log(f"{'-'*(6+10+30+20)}")
        for r in self.current_replacements:
            self.log(self._r_to_string(r))

    def _process_file(self, file_path, first_pass):
        with open(file_path, 'r') as f:
            source_code = f.read()

        index = clang.cindex.Index.create()
        args = ['-x', 'c++', '-std=c++17'] + self.include_paths
        options = clang.cindex.TranslationUnit.PARSE_INCOMPLETE

        # attempt to parse current file with clang
        try:
            tu = index.parse(file_path, args=args, options=options)
        except clang.cindex.TranslationUnitLoadError:
            print(f"Clang failed to parse {file_path}")
            return

        # print error info if issues with parsing
        for diag in tu.diagnostics:
            print(f"Message: {diag.spelling}")

        self.current_replacements = []
        self.current_source = source_code
        self.current_file = file_path

        # this is wasteful since I'm building the list on the first time when I don't need
        # to be, but I can fix it later if it's too slow
        self._build_replacements(tu.cursor)

        if not first_pass:
            self._make_replacements()
            self._write_file(self.current_file)


    def _build_replacements(self, cursor, indent=0):
        # only check it if it's in the file we're currently looking at
        # majorly speeds up gooberizing, and fixes issues with macros
        if cursor.location.file:
            cursor_file = os.path.abspath(cursor.location.file.name)
            current_file = os.path.abspath(self.current_file)

            if cursor_file != current_file:
                return

        # skip this node if it can't be renamed, but not its children
        if not self._can_be_renamed(cursor):
            for child in cursor.get_children():
                self._build_replacements(child, indent + 1)
            return

        # print node info
        self.log(f"{'  ' * indent}{cursor.kind.name}: '{cursor.spelling}' @ {str(cursor.location)}")

        # if declaring for the first time, add it to map
        if self._is_declaration(cursor.kind.name):
            if cursor.get_usr() not in self.goober_map:
                # only add to map if we haven't seen it before
                self.goober_map[cursor.get_usr()] = "goober_" + str(self.goober_n)
                self.goober_n += 1

            # always add replacement
            self._add_replacement(cursor, cursor.spelling, cursor.get_usr())

        # if using existing declaration, check for it in map
        # add it to replacements list if it exists
        elif self._is_reference(cursor.kind.name):
            # check if reference can be renamed first
            if not self._can_be_renamed(cursor.referenced):
                for child in cursor.get_children():
                    self._build_replacements(child, indent + 1)
                return

            if cursor.referenced.get_usr() in self.goober_map:
                self._add_replacement(cursor, cursor.referenced.spelling, cursor.referenced.get_usr())

            elif self._check_user_code(cursor.referenced):
                # add original to map if we haven't seen it yet and it's a user declaration
                self.goober_map[cursor.referenced.get_usr()] = "goober_" + str(self.goober_n)
                self.goober_n += 1

                self._add_replacement(cursor, cursor.referenced.spelling, cursor.referenced.get_usr())

        # if it's a constructor, we check for parent class, since it'll always have been
        # delcared before the constructor
        elif cursor.kind.name == "CONSTRUCTOR":
            parent = cursor.semantic_parent

            if parent.get_usr() in self.goober_map:
                self.goober_map[cursor.get_usr()] = self.goober_map[parent.get_usr()]
                self._add_replacement(cursor, parent.spelling, cursor.get_usr())

        # same idea with destructor
        elif cursor.kind.name == "DESTRUCTOR":
            parent = cursor.semantic_parent

            if parent.get_usr() in self.goober_map:
                self.goober_map[cursor.get_usr()] = self.goober_map[parent.get_usr()]
                self._add_replacement(cursor, parent.spelling, cursor.get_usr())

        # recursive call
        for child in cursor.get_children():
            self._build_replacements(child, indent + 1)

    def _make_replacements(self):
        # sort replacements by start then end pos
        self.current_replacements.sort(key=lambda x: (x['start'], x['end']))

        unique_replacements = []
        last_end = -1

        # create unique list of replacements, skipping overlapping ones
        for r in self.current_replacements:
            # skip if start is before the end of previous
            if r['start'] < last_end:
                continue

            unique_replacements.append(r)
            last_end = r['end']

        self.current_replacements = unique_replacements
        self.current_replacements.sort(key=lambda x: x['start'], reverse=True)

        # replace every instance in replacement_list
        for r in self.current_replacements:
            start = r['start']
            end = r['end']
            name = r['goober']

            self.current_source = self.current_source[:start] + name + self.current_source[end:]

    # write file original_path with new contents current_source to new output output_dir/filename
    def _write_file(self, original_path):
        filename = os.path.basename(original_path)
        out_path = os.path.join(self.output_dir, filename)

        try:
            with open(out_path, 'w') as f:
                f.write(self.current_source)
            print(f"Successfully gooberized {filename} as {out_path}")
        except Exception as e:
            print(f"Error: {e}")

    # add entry to replacement list for current file
    def _add_replacement(self, cursor, original_name, usr):
        # start_pos = cursor.location.offset + offset
        start_pos = self._get_accurate_offset(cursor, original_name)
        end_pos = start_pos + len(original_name)

        # make sure what's being replaced is actually correct
        actual_text = self.current_source[start_pos:end_pos]
        if actual_text != original_name:
            return

        self.current_replacements.append({
            'start': start_pos,
            'end': end_pos,
            'goober': self.goober_map[usr],
            'line': cursor.location.line,
            'col': cursor.location.column,
            'original': original_name,
            'usr': usr
        })

    # all checks for whether a cursor can be renamed
    def _can_be_renamed(self, def_cursor):
        if not def_cursor:
            return False

        if def_cursor.location.file is None:
            return False

        if not self._check_user_code(def_cursor):
            return False

        if self._is_entry_point(def_cursor):
            return False

        if self._is_cpp_operator(def_cursor.spelling):
            return False

        if def_cursor.spelling == "":
            return False

        # skip virtual methods since they can cause issues
        if def_cursor.kind.name == "CXX_METHOD":
            if def_cursor.is_virtual_method():
                return False

        return True

    # used for handling issues with macro offsets (and destructors)
    def _get_accurate_offset(self, cursor, expected_name):
        try:
            tokens = list(cursor.get_tokens())
        except:
            return cursor.location.offset

        for token in tokens:
            if token.spelling == expected_name:
                return token.location.offset

        return cursor.location.offset

    def _is_declaration(self, kind):
        return kind in [
            "VAR_DECL",
            "PARM_DECL",
            "FUNCTION_DECL",
            "CLASS_DECL",
            "STRUCT_DECL",
            "ENUM_DECL",
            "ENUM_CONSTANT_DECL",
            "CXX_METHOD",
            "FIELD_DECL",
            "TYPEDEF_DECL",
            "TYPE_ALIAS_DECL"
        ]

    def _is_reference(self, kind):
        return kind in [
            "DECL_REF_EXPR",
            "MEMBER_REF_EXPR",
            "MEMBER_REF",
            "TYPE_REF",
            "CALL_EXPR",
            "OVERLOADED_DECL_REF",
            "CXX_CTOR_INITIALIZER"
        ]

    def _check_user_code(self, cursor):
        if not cursor.location.file:
            return False

        cursor_abs = os.path.abspath(cursor.location.file.name)
        return cursor_abs in self.files

    # checks that we're not looking at the main function
    def _is_entry_point(self, cursor):
        if cursor.spelling != "main":
            return False

        if cursor.semantic_parent.kind == clang.cindex.CursorKind.TRANSLATION_UNIT or \
           cursor.semantic_parent.kind == clang.cindex.CursorKind.LINKAGE_SPEC:
            return True

        return False

    # regex to check for operators
    def _is_cpp_operator(self, name):
        return bool(re.match(r'^operator\W', name))

    # put replacement list entry in table form
    def _r_to_string(self, r):
        return f"{r['line']:<6}{str(r['col'])+'-'+str(r['col'] + r['end'] - r['start']):<10}{r['original']:<30}{r['goober']:<20}{r['usr']}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gooberize C++ code")

    parser.add_argument('files', nargs="+", help="Input files (*.cpp, *.h/*.hpp, etc.)")

    parser.add_argument('-o', '--output', default="gooberized", help="Output directory (default: gooberized)")
    parser.add_argument("-v", "--verbose", action='store_true', help="Enable verbose logging")

    args = parser.parse_args()

    expanded_files = []
    for pattern in args.files:
        matched = glob.glob(pattern, recursive=True)
        if not matched:
            print(f"No files found matching {pattern}")
            continue
        expanded_files.extend(matched)

    expanded_files = sorted(list(set(expanded_files)))

    if not expanded_files:
        print("Error: no valid input files given")
        sys.exit(1)

    # get preprocessor args
    print("Getting system include paths")
    include_paths = get_system_include_paths()

    gb = Gooberizer(expanded_files, include_paths, args.output, args.verbose)
    gb.run()
