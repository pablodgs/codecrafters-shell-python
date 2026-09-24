import unittest

from app.parsing import TokenKind, parse


class ParserTests(unittest.TestCase):
    def test_parses_pipeline_and_redirections(self) -> None:
        result = parse("echo input | cat < source >> output")

        self.assertIsNone(result.error)
        self.assertFalse(result.incomplete)
        self.assertEqual(len(result.pipeline.commands), 2)
        first, second = result.pipeline.commands
        self.assertEqual([word.text for word in first.words], ["echo", "input"])
        self.assertEqual([word.text for word in second.words], ["cat"])
        self.assertEqual(
            [(redirection.operator, redirection.target.text) for redirection in second.redirections],
            [
                (TokenKind.REDIRECT_INPUT, "source"),
                (TokenKind.REDIRECT_APPEND, "output"),
            ],
        )

    def test_recognizes_adjacent_numeric_redirection_descriptor(self) -> None:
        result = parse("echo Hello Alice 1> /tmp/pig/cow.md")

        self.assertIsNone(result.error)
        command = result.pipeline.commands[0]
        self.assertEqual([word.text for word in command.words], ["echo", "Hello", "Alice"])
        self.assertEqual(len(command.redirections), 1)
        self.assertEqual(command.redirections[0].fd, 1)
        self.assertEqual(command.redirections[0].target.text, "/tmp/pig/cow.md")

    def test_separated_or_quoted_digits_remain_command_arguments(self) -> None:
        separated = parse("echo 1 > output")
        quoted = parse("echo '1'> output")

        self.assertEqual([word.text for word in separated.pipeline.commands[0].words], ["echo", "1"])
        self.assertEqual([word.text for word in quoted.pipeline.commands[0].words], ["echo", "1"])

    def test_reports_incomplete_pipeline_and_redirection(self) -> None:
        pipeline = parse("echo input |")
        redirection = parse("echo >")

        self.assertTrue(pipeline.incomplete)
        self.assertEqual(pipeline.expected, "command")
        self.assertTrue(redirection.incomplete)
        self.assertEqual(redirection.expected, "redirection target")

    def test_preserves_partial_command_for_unterminated_quote(self) -> None:
        result = parse("echo 'unfinished")

        self.assertTrue(result.incomplete)
        self.assertEqual(result.pipeline.commands[0].words[1].text, "unfinished")

    def test_rejects_pipe_without_preceding_command(self) -> None:
        result = parse("| echo")

        self.assertEqual(result.error, "expected a command before pipe")
        self.assertFalse(result.incomplete)


if __name__ == "__main__":
    unittest.main()