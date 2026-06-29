import sys


def main():
    sys.stdout.write("$ ")

    # Read user input from standard input
    user_input = sys.stdin.readline()
    user_command = user_input

    sys.stdout.write(f"{user_command}: command not found\n")

    pass


if __name__ == "__main__":
    main()
