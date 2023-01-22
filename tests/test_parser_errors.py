import pytest

from cql.parser import CQLParser
from cql.parser import CQLParserError

# ---------------------------------------------------------------------------


def test_parser_parenthesis(parser: CQLParser):
    query = "( apple"
    with pytest.raises(
        CQLParserError, match=r"Missing closing parenthesis at position"
    ) as exc_info:
        parser.parse(query)

    query = "( apple OR banana"
    with pytest.raises(
        CQLParserError, match=r"Missing closing parenthesis at position"
    ) as exc_info:
        parser.parse(query)

    query = "( apple = 2"
    with pytest.raises(
        CQLParserError, match=r"Missing closing parenthesis at position"
    ) as exc_info:
        parser.parse(query)

    query = "( apple = 2 sortby key"
    # with pytest.raises(
    #     CQLParseError, match=r"Missing closing parenthesis at position"
    # ) as exc_info:
    #     parser.run(query)


def test_parser_scopedClause(parser: CQLParser):
    query = "apple OR"
    with pytest.raises(
        CQLParserError, match=r"Missing right side for scopedClause at position"
    ) as exc_info:
        parser.parse(query)

    query = "( apple OR"
    with pytest.raises(
        CQLParserError, match=r"Missing right side for scopedClause at position"
    ) as exc_info:
        parser.parse(query)


# ---------------------------------------------------------------------------
