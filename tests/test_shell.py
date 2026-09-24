import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import nullcontext
from pathlib import Path
from unittest.mock import patch

from app import main as shell_main
from app.execution import executor


class ShellBehaviorTests(unittest.TestCase):
    def run_shell_process(self, input_text: str, cwd: str | None = None) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        project_root = str(Path(__file__).resolve().parents[1])
        environment["PYTHONPATH"] = os.pathsep.join(
            filter(None, (project_root, environment.get("PYTHONPATH", "")))
        )
        return subprocess.run(
            [sys.executable, "-m", "app.main"],
            input=input_text,
            text=True,
            capture_output=True,
            cwd=cwd,
            env=environment,
            check=False,
        )

    def run_shell(
        self,
        input_text: str,
        executables: dict[str, str] | None = None,
        cwd: str | None = None,
    ) -> tuple[str, object]:
        output = io.StringIO()
        cwd_context = (
            patch.object(executor.os, "getcwd", return_value=cwd)
            if cwd is not None
            else nullcontext()
        )

        with (
            patch.object(sys, "stdin", io.StringIO(input_text)),
            patch.object(sys, "stdout", output),
            patch.object(executor, "find_executables", return_value=executables or {}),
            patch.object(executor.subprocess, "run") as external_run,
            cwd_context,
        ):
            shell_main.main()

        return output.getvalue(), external_run

    def test_builtins_handle_quotes_whitespace_and_pwd(self) -> None:
        output, _ = self.run_shell(
            "echo 'hello world'\necho hello   world\necho hello   \npwd\nexit\n",
            cwd="/tmp/shell-test",
        )

        self.assertEqual(
            output,
            "$ hello world\n"
            "$ hello world\n"
            "$ hello\n"
            "$ /tmp/shell-test\n"
            "$ ",
        )

    def test_external_command_receives_quoted_argument_as_one_value(self) -> None:
        output, external_run = self.run_shell(
            "demo 'two words'\nexit\n",
            executables={"demo": "/bin/demo"},
        )

        self.assertEqual(output, "$ $ ")
        external_run.assert_called_once()
        self.assertEqual(external_run.call_args.args[0], ["demo", "two words"])

    def test_repl_expands_parameters_with_quote_sensitive_splitting(self) -> None:
        with patch.dict(executor.os.environ, {"TEST_VALUE": "red  blue"}):
            output, _ = self.run_shell(
                'echo "$TEST_VALUE"\necho $TEST_VALUE\necho \'$TEST_VALUE\'\necho $MISSING\nexit\n'
            )

        self.assertEqual(
            output,
            "$ red  blue\n"
            "$ red blue\n"
            "$ $TEST_VALUE\n"
            "$ \n"
            "$ ",
        )

    def test_pipeline_connects_builtin_output_to_external_command(self) -> None:
        result = self.run_shell_process("echo pipe-data | tr a-z A-Z\nexit\n")

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "$ PIPE-DATA\n$ ")
        self.assertEqual(result.stderr, "")

    def test_redirection_overwrites_appends_and_reads_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "output.txt"
            commands = (
                f"echo first > {output_path}\n"
                f"echo second >> {output_path}\n"
                f"cat < {output_path}\n"
                "exit\n"
            )

            result = self.run_shell_process(commands)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "$ $ $ first\nsecond\n$ ")
        self.assertEqual(result.stderr, "")

    def test_stateful_builtin_in_pipeline_does_not_change_parent_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_shell_process("cd / | cat\npwd\nexit\n", cwd=directory)

        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, f"$ $ {directory}\n$ ")
        self.assertEqual(result.stderr, "")

    def test_type_and_cd_builtins_work_through_registry(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_shell_process(
                f"type cd\ntype echo\ncd {directory}\npwd\nexit\n"
            )

        self.assertEqual(result.returncode, 0)
        self.assertEqual(
            result.stdout,
            f"$ cd is a shell builtin\n$ echo is a shell builtin\n$ $ {directory}\n$ ",
        )
        self.assertEqual(result.stderr, "")

    def test_unknown_command_reports_error(self) -> None:
        output, external_run = self.run_shell("missing-command\nexit\n")

        self.assertEqual(output, "$ missing-command: command not found\n$ ")
        external_run.assert_not_called()


if __name__ == "__main__":
    unittest.main()