import sys
import os
import subprocess
from app.programs.type import call_type_program
from app.routines.find_executables import find_executables
from app.programs.cd import cd
from app.routines.process_user_input import process_user_input


def main():
    set_of_builtin_commands: set[str] = {"exit", "echo", "type", "pwd", "cd"}
    path: str = os.environ.get("PATH", "")

    # REPL loop
    while True:
        sys.stdout.write("$ ")

        # Read user input from standard input
        raw_user_input = sys.stdin.readline()
        parsed_values = process_user_input(raw_user_input)
        user_command = parsed_values.command
        user_args = [value for _, value in parsed_values.parsed_values[1:]]
        raw_args = parsed_values.raw_args
        
        # Handle user commands
        if user_command == "exit":
            break
        elif user_command == "echo":
            sys.stdout.write(f"{raw_args}\n")
        elif user_command == "type":
            call_type_program(set_of_builtin_commands, user_args, path)
        elif user_command == "pwd":
            sys.stdout.write(f"{os.getcwd()}\n")
        elif user_command == "cd":
            cd(' '.join(user_args))
        else:
            list_of_executables = find_executables(path)
            print(f"user_args: {user_args}")
            # Execute the command if it is found in the list of executables
            if user_command in list_of_executables:
                subprocess.run([user_command] + user_args)
            else:
                sys.stdout.write(f"{user_command}: command not found\n")


if __name__ == "__main__":
    main()
