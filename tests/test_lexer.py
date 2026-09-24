import unittest

from app.parsing import QuoteContext, TokenKind, lex


class LexerTests(unittest.TestCase):
    def test_lexes_words_pipes_and_redirections(self) -> None:
        result = lex("echo input | cat < source >> output")

        self.assertEqual(
            [token.kind for token in result.tokens],
            [
                TokenKind.WORD,
                TokenKind.WORD,
                TokenKind.PIPE,
                TokenKind.WORD,
                TokenKind.REDIRECT_INPUT,
                TokenKind.WORD,
                TokenKind.REDIRECT_APPEND,
                TokenKind.WORD,
            ],
        )
        self.assertEqual(
            [token.value.text for token in result.tokens if token.value is not None],
            ["echo", "input", "cat", "source", "output"],
        )
        self.assertFalse(result.incomplete)

    def test_preserves_adjacent_quote_context_and_empty_quoted_words(self) -> None:
        result = lex("pre\"$HOME\"'fix' ''")
        words = [token.value for token in result.tokens]

        self.assertEqual([word.text for word in words if word is not None], ["pre$HOMEfix", ""])
        first_word = words[0]
        self.assertIsNotNone(first_word)
        self.assertEqual(
            [part.quote_context for part in first_word.parts],
            [
                QuoteContext.UNQUOTED,
                QuoteContext.DOUBLE_QUOTED,
                QuoteContext.SINGLE_QUOTED,
            ],
        )

    def test_escaped_operators_are_word_content(self) -> None:
        result = lex(r'echo \| \"quoted\"')

        self.assertEqual(
            [token.kind for token in result.tokens],
            [TokenKind.WORD, TokenKind.WORD, TokenKind.WORD],
        )
        self.assertEqual(
            [token.value.text for token in result.tokens if token.value is not None],
            ["echo", "|", '"quoted"'],
        )
        self.assertEqual(
            result.tokens[1].value.parts[0].quote_context,
            QuoteContext.ESCAPED_UNQUOTED,
        )

    def test_removes_backslash_newline_outside_and_inside_double_quotes(self) -> None:
        source = "echo one\\\ntwo \"three\\\nfour\""

        result = lex(source)

        self.assertEqual(
            [token.value.text for token in result.tokens if token.value is not None],
            ["echo", "onetwo", "threefour"],
        )

    def test_reports_unterminated_quote_and_trailing_escape_as_incomplete(self) -> None:
        unterminated_quote = lex("echo 'unfinished")
        trailing_escape = lex("echo \\")

        self.assertTrue(unterminated_quote.incomplete)
        self.assertEqual(unterminated_quote.tokens[-1].value.text, "unfinished")
        self.assertTrue(trailing_escape.incomplete)

    def test_parser_source_positions_cover_original_input(self) -> None:
        result = lex("echo 'two words'")
        words = [token.value for token in result.tokens]

        self.assertEqual((words[0].start, words[0].end), (0, 4))
        self.assertEqual((words[1].start, words[1].end), (5, 16))
        self.assertEqual((words[1].parts[0].start, words[1].parts[0].end), (6, 15))


if __name__ == "__main__":
    unittest.main()