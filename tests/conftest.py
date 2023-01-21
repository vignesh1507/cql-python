import logging

import pytest

import cql.lexer
import cql.parser

# ---------------------------------------------------------------------------


@pytest.fixture(scope="function")
def lexer():
    """CQLLexer"""

    cqllexer = cql.lexer.CQLLexer()
    cqllexer.build(debug=True, debuglog=logging.getLogger("CQLLexer"))

    return cqllexer


@pytest.fixture(scope="function")
def parser11(lexer):
    """CQLParser 1.1"""

    cqlparser = cql.parser.CQLParser11()
    cqlparser.build(lexer)  # , debug=True, debuglog=logging.getLogger("CQLParser"))

    return cqlparser


@pytest.fixture(scope="function")
def parser12(lexer):
    """CQLParser 1.2"""

    cqlparser = cql.parser.CQLParser12()
    cqlparser.build(lexer)  # , debug=True, debuglog=logging.getLogger("CQLParser"))

    return cqlparser


@pytest.fixture(scope="function")
def parser(parser12):
    """CQLParser 1.2"""

    return parser12


# ---------------------------------------------------------------------------
