import sys
import os
from app.programs.type import call_type_program


def main():
    set_of_builtin_commands = {"exit", "echo", "type"}
    path = os.environ.get("PATH", "")

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
            sys.stdout.write(f"{user_command}: command not found\n")


if __name__ == "__main__":
    main()
