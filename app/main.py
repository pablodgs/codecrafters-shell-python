import sys


def main():
    # REPL loop
    while True:
        sys.stdout.write("$ ")

        # Read user input from standard input
        user_input = sys.stdin.readline().strip()

        if user_input == "exit":
            break
        else:
            sys.stdout.write(f"{user_input}: command not found\n")


if __name__ == "__main__":
    main()
