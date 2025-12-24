import os, sys
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
        self.file_paths = file_paths
        self.replacement_list = []
        self.goober_map = {}
        self.goober_n = 0
        self.source_code = ""

        # get source code as a string
        try:
            with open(files[0], 'r') as file:
                self.source_code = file.read()
        except Exception as e:
            print(f"Error: {e}")

        # set up clang pipeline
        index = clang.cindex.Index.create()
        args = ['-std=c++17'] + include_paths
        self.tu = index.parse(files[0], args=args)

        # print include info
        for diag in self.tu.diagnostics:
            print(f"DIAGNOSTIC: {diag.spelling}")

    def run(self):
        self._build_replacements(self.tu.cursor)
        self._make_replacements()

        self.replacement_list.sort(key=lambda x: x['original'])
        # print replacement_list for debugging
        # entries: {start, end, goober, line, col, original, usr}
        print("REPLACEMENTS")
        print(f"{'line':^6}{'cols':^10}{'original':^30}{'goober':^20}{'usr_string'}")
        print(f"{'-'*(6+10+30+20)}")
        for r in self.replacement_list:
            print(self._r_to_string(r))

        self._write_files()
        # print(self.source_code)

    def _build_replacements(self, cursor, indent=0):
        # skip this node if it's not in a file
        if cursor.location.file is None:
            for child in cursor.get_children():
                self._build_replacements(child, indent + 1)
            return

        # only process the node if it's a user file
        if self._check_user_code(cursor) and not self._is_entry_point(cursor):
            print(f"{'  ' * indent}{cursor.kind.name}: '{cursor.spelling}' @ {str(cursor.location)}")

            # if declaring for the first time, add it to map
            if self._is_declaration(cursor.kind.name):
                print(f"DEF: {cursor.spelling} | USR: {cursor.get_usr()}")
                goober_string = "goober_" + str(self.goober_n)
                self.goober_map[cursor.get_usr()] = goober_string
                start_pos = cursor.location.offset
                self.replacement_list.append({
                    'start': start_pos,
                    'end': start_pos + len(cursor.spelling),
                    'goober': goober_string,
                    'line': cursor.location.line,
                    'col': cursor.location.column,
                    'original': cursor.spelling,
                    'usr': cursor.get_usr()
                })
                self.goober_n += 1

            # if using existing declaration, check for it in map
            # add it to replacements list if it exists
            if self._is_reference(cursor.kind.name):
                print(f"USE: {cursor.referenced.spelling} | Refers to USR: {cursor.referenced.get_usr()}")
                if cursor.referenced.get_usr() in self.goober_map:
                    goober_string = self.goober_map[cursor.referenced.get_usr()]
                    start_pos = cursor.location.offset
                    self.replacement_list.append({
                        'start': start_pos,
                        'end': start_pos + len(cursor.referenced.spelling),
                        'goober': goober_string,
                        'line': cursor.location.line,
                        'col': cursor.location.column,
                        'original': cursor.referenced.spelling,
                        'usr': cursor.referenced.get_usr()
                    })

        for child in cursor.get_children():
            self._build_replacements(child, indent + 1)

    def _make_replacements(self):
        # sort replacements by end pos, descending
        self.replacement_list.sort(key=lambda x: x['start'])

        unique_replacements = []
        last_start = -1

        # create unique list of replacements, skipping duplicate start pos
        for r in self.replacement_list:
            if r['start'] == last_start:
                continue

            unique_replacements.append(r)
            last_start = r['start']

        self.replacement_list = unique_replacements
        self.replacement_list.sort(key=lambda x: x['end'], reverse=True)

        # replace every instance in replacement_list
        for r in self.replacement_list:
            start = r['start']
            end = r['end']
            name = r['goober']

            self.source_code = self.source_code[:start] + name + self.source_code[end:]

    def _write_files(self):
        for file in self.file_paths:
            base, ext = os.path.splitext(file)

            out_path = f"{base}_goober{ext}"

            try:
                with open(out_path, 'w') as f:
                    f.write(self.source_code)
                print(f"Successfully gooberized {file} as {out_path}")
            except Exception as e:
                print(f"Error: {e}")


    def _is_declaration(self, kind):
        return kind in [
            "VAR_DECL",
            "PARM_DECL",
            "FUNCTION_DECL",
            "CLASS_DECL",
            "STRUCT_DECL",
            "CXX_METHOD",
            "FIELD_DECL",
            "TYPEDEF_DECL",
            "TYPE_ALIAS_DECL"
        ]

    def _is_reference(self, kind):
        return kind in [
            "DECL_REF_EXPR",
            "MEMBER_REF_EXPR",
            "TYPE_REF",
            "OVERLOADED_DECL_REF"
        ]

    def _check_user_code(self, cursor):
        if not cursor.location.file:
            return False

        cursor_abs = os.path.abspath(cursor.location.file.name)
        file_abs = os.path.abspath(self.file_paths[0])
        return cursor_abs == file_abs

    # checks that we're not looking at the main function
    def _is_entry_point(self, cursor):
        if cursor.spelling != "main":
            return False

        if cursor.semantic_parent.kind == clang.cindex.CursorKind.TRANSLATION_UNIT or \
           cursor.semantic_parent.kind == clang.cindex.CursorKind.LINKAGE_SPEC:
            return True

        return False

    def _r_to_string(self, r):
        return f"{r['line']:<6}{str(r['col'])+'-'+str(r['col'] + r['end'] - r['start']):<10}{r['original']:<30}{r['goober']:<20}{r['usr']}"

if __name__ == "__main__":
    # update to multiple files later
    files = sys.argv[1:]

    # get preprocessor args
    include_paths = get_system_include_paths()

    gb = Gooberizer(files, include_paths)
    gb.run()
