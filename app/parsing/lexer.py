from dataclasses import dataclass
from enum import Enum, auto


class TokenKind(Enum):
    WORD = auto()
    PIPE = auto()
    REDIRECT_INPUT = auto()
    REDIRECT_OUTPUT = auto()
    REDIRECT_APPEND = auto()


class QuoteContext(Enum):
    UNQUOTED = auto()
    SINGLE_QUOTED = auto()
    DOUBLE_QUOTED = auto()
    ESCAPED_UNQUOTED = auto()
    ESCAPED_DOUBLE_QUOTED = auto()


@dataclass(frozen=True)
class WordPart:
    text: str
    quote_context: QuoteContext
    start: int
    end: int


@dataclass(frozen=True)
class Word:
    parts: tuple[WordPart, ...]
    start: int
    end: int

    @property
    def text(self) -> str:
        return "".join(part.text for part in self.parts)


@dataclass(frozen=True)
class Token:
    kind: TokenKind
    value: Word | None
    start: int
    end: int


@dataclass(frozen=True)
class LexResult:
    tokens: tuple[Token, ...]
    incomplete: bool = False


def lex(source: str) -> LexResult:
    tokens: list[Token] = []
    parts: list[WordPart] = []
    part_text: list[str] = []
    part_context: QuoteContext | None = None
    part_start = 0
    word_start: int | None = None
    quote_context: QuoteContext | None = None
    quote_start = 0
    quote_has_content = False
    incomplete = False
    index = 0

    def flush_part(end: int, force_empty: bool = False) -> None:
        nonlocal part_context, part_start
        if part_context is not None:
            text = "".join(part_text)
            if text or force_empty:
                parts.append(WordPart(text, part_context, part_start, end))
        elif force_empty:
            raise RuntimeError("Cannot create an empty word part without quote context")
        part_text.clear()
        part_context = None

    def append_text(text: str, context: QuoteContext, start: int) -> None:
        nonlocal part_context, part_start
        if part_context is not context:
            flush_part(start)
            part_context = context
            part_start = start
        part_text.append(text)

    def flush_word(end: int) -> None:
        nonlocal word_start
        if word_start is None:
            return
        flush_part(end)
        word = Word(tuple(parts), word_start, end)
        tokens.append(Token(TokenKind.WORD, word, word_start, end))
        parts.clear()
        word_start = None

    while index < len(source):
        char = source[index]

        if quote_context is QuoteContext.SINGLE_QUOTED:
            if char == "'":
                if not quote_has_content:
                    parts.append(WordPart("", quote_context, quote_start, index + 1))
                else:
                    flush_part(index)
                quote_context = None
            else:
                append_text(char, quote_context, index)
                quote_has_content = True
            index += 1
            continue

        if quote_context is QuoteContext.DOUBLE_QUOTED:
            if char == '"':
                if not quote_has_content:
                    parts.append(WordPart("", quote_context, quote_start, index + 1))
                else:
                    flush_part(index)
                quote_context = None
                index += 1
                continue
            if char == "\\":
                if index + 1 == len(source):
                    incomplete = True
                    index += 1
                    continue
                following = source[index + 1]
                if following == "\n":
                    index += 2
                    continue
                if following in '$`"\\':
                    append_text(following, QuoteContext.ESCAPED_DOUBLE_QUOTED, index)
                    quote_has_content = True
                    index += 2
                    continue
            append_text(char, quote_context, index)
            quote_has_content = True
            index += 1
            continue

        if char.isspace():
            flush_word(index)
            index += 1
            continue

        if char == "'" or char == '"':
            if word_start is None:
                word_start = index
            flush_part(index)
            quote_context = (
                QuoteContext.SINGLE_QUOTED if char == "'" else QuoteContext.DOUBLE_QUOTED
            )
            quote_start = index
            quote_has_content = False
            index += 1
            continue

        if char == "\\":
            if word_start is None:
                word_start = index
            if index + 1 == len(source):
                incomplete = True
                index += 1
                continue
            if source[index + 1] == "\n":
                index += 2
                continue
            append_text(source[index + 1], QuoteContext.ESCAPED_UNQUOTED, index)
            index += 2
            continue

        operator: TokenKind | None = None
        operator_end = index + 1
        if char == "|":
            operator = TokenKind.PIPE
        elif char == "<":
            operator = TokenKind.REDIRECT_INPUT
        elif char == ">":
            if index + 1 < len(source) and source[index + 1] == ">":
                operator = TokenKind.REDIRECT_APPEND
                operator_end += 1
            else:
                operator = TokenKind.REDIRECT_OUTPUT

        if operator is not None:
            flush_word(index)
            tokens.append(Token(operator, None, index, operator_end))
            index = operator_end
            continue

        if word_start is None:
            word_start = index
        append_text(char, QuoteContext.UNQUOTED, index)
        index += 1

    if quote_context is not None:
        incomplete = True
        if not quote_has_content:
            parts.append(WordPart("", quote_context, quote_start, len(source)))
        else:
            flush_part(len(source))

    flush_word(len(source))
    return LexResult(tuple(tokens), incomplete)