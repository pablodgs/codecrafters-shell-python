import sys

try:
    import readline
except ImportError:
    readline = None

from app.completion import matching_builtin_commands
from app.expansion import expand_words
from app.execution import execute_pipeline
from app.parsing import parse

_completion_matches: tuple[str, ...] = ()


def _complete_builtin(text: str, state: int) -> str | None:
    global _completion_matches
    if readline is None:
        return None
    if state == 0:
        matches = matching_builtin_commands(readline.get_line_buffer())
        if len(matches) == 1:
            _completion_matches = matches
        else:
            _completion_matches = ()
            sys.stdout.write("\x07")
            sys.stdout.flush()
    if state < len(_completion_matches):
        match = _completion_matches[state]
        if getattr(readline, "backend", None) == "editline":
            return f"{match} "
        return match
    return None


def _read_user_input(prompt: str) -> str:
    if sys.stdin.isatty() and readline is not None:
        try:
            return input(prompt) + "\n"
        except EOFError:
            return ""
    sys.stdout.write(prompt)
    sys.stdout.flush()
    return sys.stdin.readline()


def main():
    if readline is not None:
        readline.set_completer(_complete_builtin)
        if hasattr(readline, "set_completion_append_character"):
            readline.set_completion_append_character(" ")
        if getattr(readline, "backend", None) == "editline":
            readline.parse_and_bind("bind ^I rl_complete")
        else:
            readline.parse_and_bind("tab: complete")

    # REPL loop
    while True:
        # Read user input from standard input
        raw_user_input = _read_user_input("$ ")
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
