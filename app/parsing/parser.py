from dataclasses import dataclass

from app.parsing.lexer import QuoteContext, TokenKind, Word, lex


@dataclass(frozen=True)
class Redirection:
    operator: TokenKind
    target: Word
    start: int
    fd: int


@dataclass(frozen=True)
class SimpleCommand:
    words: tuple[Word, ...]
    redirections: tuple[Redirection, ...]


@dataclass(frozen=True)
class Pipeline:
    commands: tuple[SimpleCommand, ...]


@dataclass(frozen=True)
class ParseResult:
    pipeline: Pipeline
    incomplete: bool = False
    error: str | None = None
    expected: str | None = None


def parse(source: str) -> ParseResult:
    lex_result = lex(source)
    commands: list[SimpleCommand] = []
    words: list[Word] = []
    redirections: list[Redirection] = []
    pending_redirection: tuple[TokenKind, int, int] | None = None
    saw_pipe = False

    for token in lex_result.tokens:
        if token.kind is TokenKind.WORD:
            if token.value is None:
                raise RuntimeError("Word token is missing its value")
            if pending_redirection is None:
                words.append(token.value)
            else:
                operator, start, fd = pending_redirection
                redirections.append(Redirection(operator, token.value, start, fd))
                pending_redirection = None
            continue

        if token.kind in {
            TokenKind.REDIRECT_INPUT,
            TokenKind.REDIRECT_OUTPUT,
            TokenKind.REDIRECT_APPEND,
        }:
            if pending_redirection is not None:
                return ParseResult(
                    Pipeline(tuple(commands)),
                    error="expected a word after redirection",
                )
            fd = 0 if token.kind is TokenKind.REDIRECT_INPUT else 1
            if words:
                possible_fd = words[-1]
                is_unquoted_number = (
                    possible_fd.end == token.start
                    and possible_fd.parts
                    and all(
                        part.quote_context is QuoteContext.UNQUOTED
                        for part in possible_fd.parts
                    )
                    and possible_fd.text.isascii()
                    and possible_fd.text.isdigit()
                )
                if is_unquoted_number:
                    fd = int(possible_fd.text)
                    words.pop()
            pending_redirection = (token.kind, token.start, fd)
            continue

        if pending_redirection is not None:
            return ParseResult(
                Pipeline(tuple(commands)),
                error="expected a word after redirection",
            )
        if not words and not redirections:
            return ParseResult(Pipeline(tuple(commands)), error="expected a command before pipe")

        commands.append(SimpleCommand(tuple(words), tuple(redirections)))
        words.clear()
        redirections.clear()
        saw_pipe = True

    expected: str | None = None
    incomplete = lex_result.incomplete
    if pending_redirection is not None:
        incomplete = True
        expected = "redirection target"
    elif words or redirections:
        commands.append(SimpleCommand(tuple(words), tuple(redirections)))
    elif saw_pipe:
        incomplete = True
        expected = "command"

    return ParseResult(Pipeline(tuple(commands)), incomplete, expected=expected)