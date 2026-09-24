import contextlib
import os
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from typing import TextIO

from app.expansion import expand_word, expand_words
from app.execution.builtins import BUILTIN_COMMANDS, run_builtin
from app.parsing import Pipeline, Redirection, TokenKind
from app.routines.find_executables import find_executables


class ExecutionError(ValueError):
    pass


@dataclass(frozen=True)
class ExecutionResult:
    status: int
    should_exit: bool = False


@dataclass(frozen=True)
class _PreparedCommand:
    arguments: tuple[str, ...]
    redirections: tuple[tuple[TokenKind, str, int], ...]


def _prepare_command(command, environment: Mapping[str, str]) -> _PreparedCommand:
    arguments = expand_words(command.words, environment)
    redirections: list[tuple[TokenKind, str, int]] = []
    for redirection in command.redirections:
        targets = expand_word(redirection.target, environment)
        if len(targets) != 1:
            raise ExecutionError("ambiguous redirection")
        redirections.append((redirection.operator, targets[0], redirection.fd))
    return _PreparedCommand(arguments, tuple(redirections))


def _open_redirections(
    redirections: tuple[tuple[TokenKind, str, int], ...],
    stack: contextlib.ExitStack,
) -> dict[int, TextIO]:
    streams: dict[int, TextIO] = {}
    for operator, path, fd in redirections:
        if operator is TokenKind.REDIRECT_INPUT:
            streams[fd] = stack.enter_context(open(path, "r"))
        elif operator is TokenKind.REDIRECT_OUTPUT:
            streams[fd] = stack.enter_context(open(path, "w"))
        elif operator is TokenKind.REDIRECT_APPEND:
            streams[fd] = stack.enter_context(open(path, "a"))
    return streams


def _run_single(command: _PreparedCommand, environment: Mapping[str, str]) -> int:
    with contextlib.ExitStack() as stack:
        try:
            redirected_streams = _open_redirections(command.redirections, stack)
        except OSError as error:
            sys.stderr.write(f"shell: {error}\n")
            return 1

        if not command.arguments:
            return 0

        name = command.arguments[0]
        arguments = list(command.arguments[1:])
        if name in BUILTIN_COMMANDS:
            with contextlib.ExitStack() as output_context:
                if 1 in redirected_streams:
                    output_context.enter_context(contextlib.redirect_stdout(redirected_streams[1]))
                if 2 in redirected_streams:
                    output_context.enter_context(contextlib.redirect_stderr(redirected_streams[2]))
                return run_builtin(name, arguments, environment)

        path = environment.get("PATH", "")
        if name not in find_executables(path):
            sys.stdout.write(f"{name}: command not found\n")
            return 127

        options = {}
        if 0 in redirected_streams:
            options["stdin"] = redirected_streams[0]
        if 1 in redirected_streams:
            options["stdout"] = redirected_streams[1]
        if 2 in redirected_streams:
            options["stderr"] = redirected_streams[2]
        try:
            return subprocess.run(
                list(command.arguments),
                **options,
                env=dict(environment),
                check=False,
            ).returncode
        except OSError as error:
            sys.stderr.write(f"{name}: {error}\n")
            return 126


def _child_error(message: str, status: int) -> None:
    try:
        os.write(2, message.encode())
    finally:
        os._exit(status)


def _apply_child_redirections(
    redirections: tuple[tuple[TokenKind, str, int], ...]
) -> None:
    for operator, path, target_fd in redirections:
        if operator is TokenKind.REDIRECT_INPUT:
            flags = os.O_RDONLY
        elif operator is TokenKind.REDIRECT_OUTPUT:
            flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC
        else:
            flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND
        descriptor = os.open(path, flags, 0o666)
        try:
            os.dup2(descriptor, target_fd)
        finally:
            if descriptor not in (0, 1, 2):
                os.close(descriptor)


def _run_pipeline_child(
    command: _PreparedCommand,
    environment: Mapping[str, str],
    pipe_fds: list[int],
    index: int,
    command_count: int,
) -> None:
    if index > 0:
        os.dup2(pipe_fds[(index - 1) * 2], 0)
    if index < command_count - 1:
        os.dup2(pipe_fds[index * 2 + 1], 1)

    for descriptor in pipe_fds:
        if descriptor not in (0, 1, 2):
            os.close(descriptor)

    try:
        _apply_child_redirections(command.redirections)
    except OSError as error:
        _child_error(f"shell: {error}\n", 1)

    if not command.arguments:
        os._exit(0)

    name = command.arguments[0]
    if name in BUILTIN_COMMANDS:
        status = run_builtin(name, list(command.arguments[1:]), environment)
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(status)

    if name not in find_executables(environment.get("PATH", "")):
        _child_error(f"{name}: command not found\n", 127)
    try:
        os.execvpe(name, list(command.arguments), dict(environment))
    except OSError as error:
        _child_error(f"{name}: {error}\n", 126)


def _run_pipeline(
    commands: tuple[_PreparedCommand, ...],
    environment: Mapping[str, str],
) -> int:
    pipe_fds: list[int] = []
    for _ in range(len(commands) - 1):
        pipe_fds.extend(os.pipe())

    process_ids: list[int] = []
    try:
        for index, command in enumerate(commands):
            process_id = os.fork()
            if process_id == 0:
                _run_pipeline_child(command, environment, pipe_fds, index, len(commands))
            process_ids.append(process_id)
    finally:
        for descriptor in pipe_fds:
            if descriptor not in (0, 1, 2):
                os.close(descriptor)

    status = 0
    for process_id in process_ids:
        _, wait_status = os.waitpid(process_id, 0)
        if process_id == process_ids[-1]:
            status = os.waitstatus_to_exitcode(wait_status)
    return status


def execute_pipeline(
    pipeline: Pipeline,
    environment: Mapping[str, str] | None = None,
) -> ExecutionResult:
    command_environment = environment if environment is not None else os.environ
    commands = tuple(
        _prepare_command(command, command_environment) for command in pipeline.commands
    )
    if not commands:
        return ExecutionResult(0)

    if len(commands) == 1:
        command = commands[0]
        should_exit = bool(command.arguments and command.arguments[0] == "exit")
        return ExecutionResult(_run_single(command, command_environment), should_exit)

    return ExecutionResult(_run_pipeline(commands, command_environment))