import logging
from typing import Optional

from .lexer import CQLLexer
from .parser import CQLParser11  # noqa: F401
from .parser import CQLParser12
from .parser import CQLQuery


def parse(
    query: str, debug: bool = False, debug_parser: bool = False
) -> Optional[CQLQuery]:
    if debug:
        kwargs_lexer = dict(debug=True, debuglog=logging.getLogger("CQLLexer"))
    else:
        kwargs_lexer = dict()

    if debug_parser:
        kwargs_parser = dict(debug=True, debuglog=logging.getLogger("CQLParser"))
        kwargs_parser_run = dict(tracking=True)
    else:
        kwargs_parser = dict()
        kwargs_parser_run = dict()

    cqllexer = CQLLexer()
    cqllexer.build(**kwargs_lexer)

    cqlparser = CQLParser12()
    cqlparser.build(cqllexer, **kwargs_parser)

    return cqlparser.run(query, **kwargs_parser_run)
