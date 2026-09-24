COMMAND_COMPLETION_CANDIDATES = ("echo", "exit")


def matching_builtin_commands(line_buffer: str) -> tuple[str, ...]:
    command_text = line_buffer.lstrip()
    if any(character.isspace() for character in command_text):
        return ()
    return tuple(
        command
        for command in COMMAND_COMPLETION_CANDIDATES
        if command.startswith(command_text)
    )