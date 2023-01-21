import pytest

from cql.parser import CQLParser
from cql.parser import CQLParseError


# ---------------------------------------------------------------------------


def test_parser_paranthesis(parser: CQLParser):
    query = "( apple"
    with pytest.raises(
        CQLParseError, match=r"Missing closing paranthesis at position"
    ) as exc_info:
        parser.run(query)

    query = "( apple OR banana"
    with pytest.raises(
        CQLParseError, match=r"Missing closing paranthesis at position"
    ) as exc_info:
        parser.run(query)

    query = "( apple = 2"
    with pytest.raises(
        CQLParseError, match=r"Missing closing paranthesis at position"
    ) as exc_info:
        parser.run(query)

    query = "( apple = 2 sortby key"
    # with pytest.raises(
    #     CQLParseError, match=r"Missing closing paranthesis at position"
    # ) as exc_info:
    #     parser.run(query)


def test_parser_scopedClause(parser: CQLParser):
    query = "apple OR"
    with pytest.raises(
        CQLParseError, match=r"Missing right side for scopedClause at position"
    ) as exc_info:
        parser.run(query)

    query = "( apple OR"
    with pytest.raises(
        CQLParseError, match=r"Missing right side for scopedClause at position"
    ) as exc_info:
        parser.run(query)


# ---------------------------------------------------------------------------
