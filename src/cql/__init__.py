import logging
from typing import Optional

from .lexer import CQLLexer
from .parser import CQLParser11  # noqa: F401
from .parser import CQLParser12
from .parser import CQLQuery


def parse(
    query: str,
    debug_show_lexerinfo: bool = False,
    debug_show_parserinfo: bool = False,
    debug_parsing: bool = False,
) -> Optional[CQLQuery]:
    kwargs_lexer = dict()
    kwargs_parser = dict()
    kwargs_parser_run = dict(tracking=True)

    if debug_show_lexerinfo:
        # to print initial state (rules)
        kwargs_lexer.update(dict(debug=True, debuglog=logging.getLogger("CQLLexer")))

    if debug_show_parserinfo:
        # to print initial state (grammar/rules/states)
        kwargs_parser.update(dict(debug=True, debuglog=logging.getLogger("CQLParser")))

    if debug_parsing:
        # for verbose parse step details about state/stack/action/result
        kwargs_parser_run.update(dict(debug=logging.getLogger("CQLParserSteps")))

    cqllexer = CQLLexer()
    cqllexer.build(**kwargs_lexer)

    cqlparser = CQLParser12()
    cqlparser.build(cqllexer, **kwargs_parser)

    return cqlparser.parse(query, **kwargs_parser_run)
