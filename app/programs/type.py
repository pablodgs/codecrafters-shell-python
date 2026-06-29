import sys
from app.routines.find_executables import find_executables

def call_type_program(builtins: set[str], user_args: list[str], path: str) -> None:
    map_of_executables: dict[str, str] = find_executables(path)

    for arg in user_args:
        if arg in builtins:
            sys.stdout.write(f"{arg} is a shell builtin\n")
        elif arg in map_of_executables:
            sys.stdout.write(f"{arg} is {map_of_executables[arg]}\n")
        else:
            sys.stdout.write(f"{arg} not found\n")
