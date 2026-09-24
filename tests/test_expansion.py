import unittest

from app.expansion import ExpansionError, expand_word, expand_words
from app.parsing import lex


def parse_word(source: str):
    result = lex(source)
    if result.incomplete or len(result.tokens) != 1 or result.tokens[0].value is None:
        raise AssertionError(f"expected one complete word from {source!r}")
    return result.tokens[0].value


class ParameterExpansionTests(unittest.TestCase):
    def test_expands_braced_and_unbraced_names(self) -> None:
        word = parse_word("$USER/${HOME}")

        self.assertEqual(
            expand_word(word, {"USER": "sam", "HOME": "/home/sam"}),
            ("sam//home/sam",),
        )

    def test_single_quoted_and_escaped_parameters_remain_literal(self) -> None:
        single_quoted = parse_word("'$USER'")
        escaped = parse_word(r"\$USER")

        self.assertEqual(expand_word(single_quoted, {"USER": "sam"}), ("$USER",))
        self.assertEqual(expand_word(escaped, {"USER": "sam"}), ("$USER",))

    def test_double_quoted_expansion_does_not_split(self) -> None:
        word = parse_word('"$ITEMS"')

        self.assertEqual(expand_word(word, {"ITEMS": "red blue"}), ("red blue",))

    def test_unquoted_expansion_splits_and_attaches_neighboring_text(self) -> None:
        word = parse_word("pre$ITEMS'post'")

        self.assertEqual(
            expand_word(word, {"ITEMS": "red blue"}),
            ("prered", "bluepost"),
        )

    def test_unset_unquoted_value_disappears_but_quoted_empty_is_kept(self) -> None:
        unquoted = parse_word("$MISSING")
        quoted = parse_word('"$MISSING"')

        self.assertEqual(expand_word(unquoted, {}), ())
        self.assertEqual(expand_word(quoted, {}), ("",))

    def test_explicit_empty_quotes_survive_expansion(self) -> None:
        word = parse_word("''$MISSING")

        self.assertEqual(expand_word(word, {}), ("",))

    def test_only_expansion_results_are_field_split(self) -> None:
        word = parse_word(r"before\ after$ITEMS")

        self.assertEqual(
            expand_word(word, {"ITEMS": "one two"}),
            ("before afterone", "two"),
        )

    def test_expand_words_flattens_fields_from_each_word(self) -> None:
        words = [parse_word("$ITEMS"), parse_word("tail")]

        self.assertEqual(expand_words(words, {"ITEMS": "one two"}), ("one", "two", "tail"))

    def test_rejects_malformed_braced_parameter(self) -> None:
        with self.assertRaises(ExpansionError):
            expand_word(parse_word("${ITEMS"), {"ITEMS": "value"})

        with self.assertRaises(ExpansionError):
            expand_word(parse_word("${ITEMS:-fallback}"), {"ITEMS": "value"})

        with self.assertRaises(ExpansionError):
            expand_word(parse_word("${}"), {"ITEMS": "value"})


if __name__ == "__main__":
    unittest.main()