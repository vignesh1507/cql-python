import logging
import re

import ply.lex as lex
from ply.lex import Lexer
from ply.lex import LexToken


LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------


class CQLLexer:
    #: reserved names
    reserved = {
        # r"(?i)and": "BOOL_AND",
        # r"(?i)or": "BOOL_OR",
        # r"(?i)not": "BOOL_NOT",
        # r"(?i)prox": "BOOL_PROX",
        # r"(?i)sortby": "KEY_SORTBY",
    }

    #: List of token names.
    # fmt: off
    tokens = [
        # parenthesis
        "LPAREN", "RPAREN",
        # modifier start
        "MODSTART",
        # term relations
        "LT", "LE", "GT", "GE", "NE", "EQ", "EQUALS",
        # boolean relations
        "BOOL_AND", "BOOL_OR", "BOOL_NOT", "BOOL_PROX", "KEY_SORTBY",
        # strings / identifiers
        "CHAR_STRING1", "CHAR_STRING2",
            
    ] + list(reserved.values())
    # fmt: on

    # ---------------------------------------------------

    t_LPAREN = r"\("
    t_RPAREN = r"\)"

    t_MODSTART = r"/"

    t_LT = r"<"
    t_LE = r"<="
    t_GT = r">"
    t_GE = r">="
    t_NE = r"<>"
    t_EQ = r"="
    t_EQUALS = r"=="

    # ---------------------------------------------------
    # NOTE: required? (?i)

    def t_BOOL_AND(self, tok: LexToken) -> LexToken:
        r"and"
        tok.value = tok.value.upper()
        return tok

    def t_BOOL_OR(self, tok: LexToken) -> LexToken:
        r"or"
        tok.value = tok.value.upper()
        return tok

    def t_BOOL_NOT(self, tok: LexToken) -> LexToken:
        r"not"
        tok.value = tok.value.upper()
        return tok

    def t_BOOL_PROX(self, tok: LexToken) -> LexToken:
        r"prox"
        tok.value = tok.value.upper()
        return tok

    def t_KEY_SORTBY(self, tok: LexToken) -> LexToken:
        r"sortby"
        tok.value = tok.value.lower()
        return tok

    # ---------------------------------------------------

    t_CHAR_STRING1 = r"""[^\s()=<>"/]+"""

    def t_CHAR_STRING2(self, tok: LexToken) -> LexToken:
        r"""\"[^\"]*\" """
        tok.value = tok.value.strip('"').replace('\\"', '"')
        return tok

    # ---------------------------------------------------

    #: A string containing ignored characters (spaces and tabs)
    t_ignore = " \t\r\n\f\v"

    def t_ignore_newline(self, tok: LexToken):
        r"\n+"
        tok.lexer.lineno += tok.value.count("\n")

    #: Error handling rule
    def t_error(self, tok: LexToken) -> None:
        LOGGER.warning("Illegal character '%s'", tok.value[0])
        # TODO: raise Exception? We want to be strict.
        tok.lexer.skip(1)

    # ---------------------------------------------------

    def find_column(input, token):
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


# ---------------------------------------------------------------------------
