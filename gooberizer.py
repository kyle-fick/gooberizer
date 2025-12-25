import os, sys
import re
import shutil
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
        print("Error: 'g++' command not found")
        return []


class Gooberizer:
    def __init__(self, file_paths, include_paths):
        self.files = [os.path.abspath(f) for f in file_paths]
        self.include_paths = include_paths

        self.goober_map = {}
        self.goober_n = 0

        # create gooberized output directory
        self.output_dir = "gooberized"
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
        os.makedirs(self.output_dir)


    def run(self):
        print("First pass:")
        for file_path in self.files:
            print(f"Processing {os.path.basename(file_path)}")
            self._process_file(file_path, first_pass=True)

        print("Second pass:")
        for file_path in self.files:
            print(f"Processing {os.path.basename(file_path)}")
            self._process_file(file_path, first_pass=False)

            # print replacement_list for debugging
            self.current_replacements.sort(key=lambda x: x['original'])
            print(f"REPLACEMENTS - {file_path}")
            print(f"{'line':^6}{'cols':^10}{'original':^30}{'goober':^20}{'usr_string'}")
            print(f"{'-'*(6+10+30+20)}")
            for r in self.current_replacements:
                print(self._r_to_string(r))


        # # print replacement_list for debugging
        # # print(self.source_code)

    def _process_file(self, file_path, first_pass):
        with open(file_path, 'r') as f:
            source_code = f.read()

        index = clang.cindex.Index.create()
        args = ['-std=c++17'] + self.include_paths
        tu = index.parse(file_path, args=args)

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
        if cursor.spelling == "read_header":
            pass

        if not self._can_be_renamed(cursor):
            for child in cursor.get_children():
                self._build_replacements(child, indent + 1)
            return

        print(f"{'  ' * indent}{cursor.kind.name}: '{cursor.spelling}' @ {str(cursor.location)}")

        # if declaring for the first time, add it to map
        if self._is_declaration(cursor.kind.name):
            # print(f"DEF: {cursor.spelling} | USR: {cursor.get_usr()}")
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

            # print(f"USE: {cursor.referenced.spelling} | Refers to USR: {cursor.referenced.get_usr()}")
            if cursor.referenced.get_usr() in self.goober_map:
                self._add_replacement(cursor, cursor.referenced.spelling, cursor.referenced.get_usr())

            elif self._check_user_code(cursor.referenced):
                # add original to map if we haven't seen it yet and it's a declaration
                self.goober_map[cursor.referenced.get_usr()] = "goober_" + str(self.goober_n)
                self.goober_n += 1

                self._add_replacement(cursor, cursor.referenced.spelling, cursor.referenced.get_usr())

        # if it's a constructor, we check for parent class
        elif cursor.kind.name == "CONSTRUCTOR":
            parent = cursor.semantic_parent

            if parent.get_usr() in self.goober_map:
                self.goober_map[cursor.get_usr()] = self.goober_map[parent.get_usr()]
                self._add_replacement(cursor, parent.spelling, cursor.get_usr())

        elif cursor.kind.name == "DESTRUCTOR":
            parent = cursor.semantic_parent

            if parent.get_usr() in self.goober_map:
                self.goober_map[cursor.get_usr()] = self.goober_map[parent.get_usr()]
                self._add_replacement(cursor, parent.spelling, cursor.get_usr(), 1)

        # recursive call
        for child in cursor.get_children():
            self._build_replacements(child, indent + 1)

    def _make_replacements(self):
        # sort replacements by end pos, descending
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

    def _add_replacement(self, cursor, original_name, usr, offset=0):
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

        if def_cursor.kind.name == "CXX_METHOD":
            if def_cursor.is_virtual_method():
                return False

        return True

    # used for handling issues with macro offsets
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

    def _is_cpp_operator(self, name):
        return bool(re.match(r'^operator\W', name))

    # checks if method overrides method from system header
    # def _is_system_override(self, cursor):
    #     if cursor.kind.name != "CXX_METHOD":
    #         return False
    #
    #     overrides = cursor.get_overridden_cursors()
    #
    #     for base_method in overrides:
    #         # check if any base method is a system method
    #         if not self._check_user_code(base_method):
    #             return True
    #
    #         # otherwise recursively check if it's an override of a system method
    #         if self._is_system_override(base_method):
    #             return True
    #
    #     return False

    def _r_to_string(self, r):
        return f"{r['line']:<6}{str(r['col'])+'-'+str(r['col'] + r['end'] - r['start']):<10}{r['original']:<30}{r['goober']:<20}{r['usr']}"

if __name__ == "__main__":
    # update to multiple files later
    files = sys.argv[1:]

    # get preprocessor args
    include_paths = get_system_include_paths()

    gb = Gooberizer(files, include_paths)
    gb.run()
