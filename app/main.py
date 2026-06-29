import sys
import os
from app.programs.type import call_type_program
from app.routines.find_executables import find_executables


def main():
    set_of_builtin_commands: set[str] = {"exit", "echo", "type"}
    path: str = os.environ.get("PATH", "")

    # REPL loop
    while True:
        sys.stdout.write("$ ")

        # Read user input from standard input
        user_input = sys.stdin.readline().strip()
        user_words_list = user_input.split()
        if len(user_words_list) > 0:
            user_command = user_words_list[0]
            raw_user_args = user_input[len(user_command)+1:]
            user_args = user_words_list[1:]
        else:
            user_command = ""
            raw_user_args = ""
            user_args = []
        
        # Handle user commands
        if user_command == "exit":
            break
        elif user_command == "echo":
            sys.stdout.write(f"{raw_user_args}\n")
        elif user_command == "type":
            call_type_program(set_of_builtin_commands, user_args, path)
        else:
            list_of_executables = find_executables(path)
            # Execute the command if it is found in the list of executables
            if user_command in list_of_executables:
                executable_path = list_of_executables[user_command]
                os.execv(executable_path, [user_command] + user_args)
            else:
                sys.stdout.write(f"{user_command}: command not found\n")


if __name__ == "__main__":
    main()
