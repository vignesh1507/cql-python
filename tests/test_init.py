import pytest

# ---------------------------------------------------------------------------


def test_init_imports():
    import cql
    import cql.lexer
    import cql.parser

    assert cql.parser.CQLParser == cql.CQLParser
    assert cql.parser.CQLParser11 == cql.CQLParser11
    assert cql.parser.CQLParser12 == cql.CQLParser12
    assert cql.lexer.CQLLexer == cql.CQLLexer


def test_init_parse():
    import cql

    parsed = cql.parse("dc.title any fish or dc.creator any sanderson")
    assert parsed is not None
    assert parsed.version == "1.2"


# ---------------------------------------------------------------------------
