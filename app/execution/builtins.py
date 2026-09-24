import os
import sys
from collections.abc import Mapping

from app.programs.cd import cd
from app.programs.type import call_type_program


def _echo(arguments: list[str], environment: Mapping[str, str]) -> int:
    sys.stdout.write(f"{' '.join(arguments)}\n")
    return 0


def _pwd(arguments: list[str], environment: Mapping[str, str]) -> int:
    sys.stdout.write(f"{os.getcwd()}\n")
    return 0


def _cd(arguments: list[str], environment: Mapping[str, str]) -> int:
    if len(arguments) > 1:
        sys.stderr.write("cd: too many arguments\n")
        return 1
    path = arguments[0] if arguments else environment.get("HOME", "")
    cd(path)
    return 0


def _type(arguments: list[str], environment: Mapping[str, str]) -> int:
    call_type_program(set(BUILTIN_COMMANDS), arguments, environment.get("PATH", ""))
    return 0


def _exit(arguments: list[str], environment: Mapping[str, str]) -> int:
    return 0


BUILTINS = {
    "cd": _cd,
    "echo": _echo,
    "exit": _exit,
    "pwd": _pwd,
    "type": _type,
}
BUILTIN_COMMANDS = frozenset(BUILTINS)


def run_builtin(name: str, arguments: list[str], environment: Mapping[str, str]) -> int:
    return BUILTINS[name](arguments, environment)