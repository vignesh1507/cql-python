import pytest

from cql.parser import CQLParser
from cql.parser import CQLQuery


# ---------------------------------------------------------------------------


def test_query1(parser: CQLParser):
    query = "(bar or baz)"
    parsed: CQLQuery = parser.run(query)
    assert parsed is not None


@pytest.mark.skip(reason="TODO: does the grammar even support this? <index> <rel> <bool-clause>")
def test_query2(parser: CQLParser):
    query = "author=(bar or baz)"
    parsed: CQLQuery = parser.run(query)
    assert parsed is not None

    query = "title=foo and author=(bar or baz)"
    parsed: CQLQuery = parser.run(query)
    assert parsed is not None


# ---------------------------------------------------------------------------
