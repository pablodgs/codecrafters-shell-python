from collections.abc import Mapping, Sequence

from app.parsing.lexer import QuoteContext, Word


class ExpansionError(ValueError):
    pass


def _variable_end(text: str, start: int) -> int:
    if start >= len(text) or not (
        text[start] == "_" or "A" <= text[start] <= "Z" or "a" <= text[start] <= "z"
    ):
        return start

    end = start + 1
    while end < len(text):
        char = text[end]
        if char == "_" or "A" <= char <= "Z" or "a" <= char <= "z" or "0" <= char <= "9":
            end += 1
        else:
            break
    return end


def _fragments(text: str, environment: Mapping[str, str]):
    literal_start = 0
    index = 0

    while index < len(text):
        if text[index] != "$" or index + 1 == len(text):
            index += 1
            continue

        if text[index + 1] == "{":
            closing_brace = text.find("}", index + 2)
            if closing_brace == -1:
                raise ExpansionError("unterminated parameter expansion")
            name = text[index + 2 : closing_brace]
            if not name or _variable_end(name, 0) != len(name):
                raise ExpansionError(f"unsupported parameter expansion: ${{{name}}}")
            if literal_start < index:
                yield text[literal_start:index], False
            yield environment.get(name, ""), True
            index = closing_brace + 1
            literal_start = index
            continue

        name_end = _variable_end(text, index + 1)
        if name_end == index + 1:
            index += 1
            continue
        if literal_start < index:
            yield text[literal_start:index], False
        yield environment.get(text[index + 1 : name_end], ""), True
        index = name_end
        literal_start = index

    if literal_start < len(text):
        yield text[literal_start:], False


def expand_word(word: Word, environment: Mapping[str, str]) -> tuple[str, ...]:
    """Expand named parameters, then split unquoted values on default IFS whitespace."""
    fields: list[str] = []
    current: list[str] = []
    current_forced = False

    def finish_field() -> None:
        nonlocal current_forced
        fields.append("".join(current))
        current.clear()
        current_forced = False

    def append_literal(text: str, force_empty: bool = False) -> None:
        nonlocal current_forced
        current.append(text)
        current_forced = current_forced or bool(text) or force_empty

    def append_unquoted_expansion(text: str) -> None:
        for char in text:
            if char in " \t\n":
                if current or current_forced:
                    finish_field()
            else:
                append_literal(char)

    for part in word.parts:
        context = part.quote_context
        if context in {
            QuoteContext.SINGLE_QUOTED,
            QuoteContext.ESCAPED_UNQUOTED,
            QuoteContext.ESCAPED_DOUBLE_QUOTED,
        }:
            append_literal(part.text, force_empty=context is QuoteContext.SINGLE_QUOTED)
            continue

        is_double_quoted = context is QuoteContext.DOUBLE_QUOTED
        for text, is_parameter in _fragments(part.text, environment):
            if is_parameter and not is_double_quoted:
                append_unquoted_expansion(text)
            else:
                append_literal(text, force_empty=is_parameter and is_double_quoted)

        if is_double_quoted and not part.text:
            current_forced = True

    if current or current_forced:
        finish_field()
    return tuple(fields)


def expand_words(
    words: Sequence[Word], environment: Mapping[str, str]
) -> tuple[str, ...]:
    return tuple(field for word in words for field in expand_word(word, environment))