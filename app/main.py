import sys
from app.expansion import expand_words
from app.execution import execute_pipeline
from app.parsing import parse


def main():
    # REPL loop
    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()

        # Read user input from standard input
        raw_user_input = sys.stdin.readline()
        if not raw_user_input:
            break

        parsed_input = parse(raw_user_input)
        if parsed_input.error is not None:
            sys.stdout.write(f"syntax error: {parsed_input.error}\n")
            continue
        if parsed_input.incomplete:
            sys.stdout.write("syntax error: incomplete input\n")
            continue
        if not parsed_input.pipeline.commands:
            continue
        try:
            result = execute_pipeline(parsed_input.pipeline)
        except ValueError as error:
            sys.stderr.write(f"shell: {error}\n")
            continue
        if result.should_exit:
            break


if __name__ == "__main__":
    main()
