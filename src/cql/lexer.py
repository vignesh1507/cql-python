import logging
import re

import cql._vendor.ply.lex as lex
from cql._vendor.ply.lex import Lexer
from cql._vendor.ply.lex import LexToken

LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------


class CQLLexerError(Exception):
    pass


# ---------------------------------------------------------------------------


class CQLLexer:
    #: reserved names
    reserved = {
        "and": "AND",
        "or": "OR",
        "not": "NOT",
        "prox": "PROX",
        "sortby": "SORTBY",
    }

    #: List of token names.
    # fmt: off
    tokens = [
        # parenthesis
        "LPAREN", "RPAREN",
        # modifier start
        "MODSTART",
        # term relations
        "LE", "GE", "LT", "GT", "NE", "EQUALS", "EQ",
        # strings / identifiers
        "CHAR_STRING1", "CHAR_STRING2",
        # boolean relations
    ] + list(reserved.values())
    # fmt: on

    # ---------------------------------------------------

    t_LPAREN = r"\("
    t_RPAREN = r"\)"

    t_MODSTART = r"/"

    t_LE = r"<="
    t_LT = r"<"
    t_GE = r">="
    t_GT = r">"
    t_NE = r"<>"
    t_EQUALS = r"=="
    t_EQ = r"="

    # ---------------------------------------------------

    def t_CHAR_STRING1(self, tok: LexToken) -> LexToken:
        r"""[^\s()=<>"/]+"""
        # check for keywords (as in §4.3 / https://stackoverflow.com/a/39628385/9360161)
        tok.type = self.reserved.get(tok.value.lower(), tok.type)
        return tok

    def t_CHAR_STRING2(self, tok: LexToken) -> LexToken:
        r'''"(?:\\"|[^"])*"'''
        tok.value = tok.value[1:-1].replace('\\"', '"')
        return tok

    # ---------------------------------------------------

    #: A string containing ignored characters (spaces, tabs, and newlines)
    t_ignore = " \t\r\n\f\v"

    #: Error handling rule
    def t_error(self, tok: LexToken) -> None:
        LOGGER.error("Illegal character '%s' at %s", tok.value[0], tok.lexpos)
        raise CQLLexerError(f"Illegal character {tok.value[0]!r} at {tok.lexpos}", tok)

    # ---------------------------------------------------

    def find_column(self, token: LexToken) -> int:
        input = self.lexer.lexdata
        line_start = input.rfind("\n", 0, token.lexpos) + 1
        return (token.lexpos - line_start) + 1

    def build(self, **kwargs) -> None:
        self.lexer: Lexer = lex.lex(
            module=self, reflags=re.UNICODE | re.VERBOSE | re.IGNORECASE, **kwargs
        )

    def run(self, content: str, skip: int = 0, limit: int = 30):
        self.lexer.input(content)

        cnt: int = 0
        while True:
            tok: LexToken = self.lexer.token()
            if not tok:
                break

            cnt += 1
            if cnt <= skip:
                continue
            if cnt - skip > limit:
                break

            yield tok
