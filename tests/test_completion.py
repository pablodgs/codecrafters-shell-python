import os
import pty
import select
import subprocess
import time
import unittest
from pathlib import Path

from app.completion import matching_builtin_commands

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_interactive_shell(actions: list[tuple[bytes, bytes | None]]) -> tuple[bytes, int]:
    master_fd, slave_fd = pty.openpty()
    environment = os.environ.copy()
    environment["PYTHONPATH"] = os.pathsep.join(
        filter(None, (str(PROJECT_ROOT), environment.get("PYTHONPATH", "")))
    )
    process = subprocess.Popen(
        [str(PROJECT_ROOT / "your_program.sh")],
        cwd=PROJECT_ROOT,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        env=environment,
        close_fds=True,
    )
    os.close(slave_fd)
    output = bytearray()

    def read_until(predicate, timeout: float = 5.0) -> bool:
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline and not predicate(output):
            readable, _, _ = select.select(
                [master_fd], [], [], max(0.0, deadline - time.monotonic())
            )
            if not readable:
                break
            try:
                output.extend(os.read(master_fd, 4096))
            except OSError:
                break
        return predicate(output)

    try:
        if not read_until(lambda data: b"$ " in data):
            raise AssertionError("shell did not display its initial prompt")
        for payload, expected in actions:
            os.write(master_fd, payload)
            if expected is not None and not read_until(lambda data: expected in data):
                raise AssertionError(f"interactive shell did not produce {expected!r}")
        status = process.wait(timeout=5)
        read_until(lambda _: False, timeout=0.05)
        return bytes(output), status
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        os.close(master_fd)


class CommandCompletionTests(unittest.TestCase):
    def test_returns_unique_builtin_prefix_matches(self) -> None:
        self.assertEqual(matching_builtin_commands("ech"), ("echo",))
        self.assertEqual(matching_builtin_commands("exi"), ("exit",))
        self.assertEqual(matching_builtin_commands("echo"), ("echo",))

    def test_keeps_ambiguous_and_unmatched_input_uncompleted(self) -> None:
        self.assertEqual(matching_builtin_commands("e"), ("echo", "exit"))
        self.assertEqual(matching_builtin_commands("unknown"), ())

    def test_only_completes_a_command_word(self) -> None:
        self.assertEqual(matching_builtin_commands("echo arg"), ())
        self.assertEqual(matching_builtin_commands("  ech"), ("echo",))

    def test_tab_completes_echo_and_adds_space(self) -> None:
        output, status = run_interactive_shell(
            [(b"ech\tHello\n", b"Hello\r\n"), (b"exit\n", None)]
        )

        self.assertEqual(status, 0)
        self.assertIn(b"echo Hello\r\n", output)

    def test_unknown_command_keeps_text_and_rings_bell(self) -> None:
        output, status = run_interactive_shell(
            [
                (b"zz\t", b"\x07"),
                (b"\n", b"zz: command not found"),
                (b"exit\n", None),
            ]
        )

        self.assertEqual(status, 0)
        self.assertIn(b"\x07", output)
        self.assertIn(b"zz: command not found", output)

    def test_tab_completes_exit(self) -> None:
        output, status = run_interactive_shell([(b"exi\t\n", None)])

        self.assertEqual(status, 0)
        self.assertIn(b"exit ", output)


if __name__ == "__main__":
    unittest.main()