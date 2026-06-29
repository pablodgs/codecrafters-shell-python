import sys
import os

def call_type_program(builtins: set[str], user_args: list[str], path: str) -> None:
    list_of_path_directories: list[str] = path.split(os.pathsep)
    map_of_executables: dict[str, str] = {}
    for directory in list_of_path_directories:
        if os.path.isdir(directory):
            for file in os.listdir(directory):
                file_path = os.path.join(directory, file)
                if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
                    map_of_executables[file] = file_path

    for arg in user_args:
        if arg in builtins:
            sys.stdout.write(f"{arg} is a shell builtin\n")
        elif arg in map_of_executables:
            sys.stdout.write(f"{arg} is {map_of_executables[arg]}\n")
        else:
            sys.stdout.write(f"{arg} not found\n")
