import pytest

# ---------------------------------------------------------------------------


def test_init_imports():
    import cql
    import cql.lexer
    import cql.parser

    # assert cql.parser.CQLParser == cql.CQLParser
    assert cql.parser.CQLParser11 == cql.CQLParser11
    assert cql.parser.CQLParser12 == cql.CQLParser12
    assert cql.lexer.CQLLexer == cql.CQLLexer


def test_init_parse():
    import cql

    parsed = cql.parse("dc.title any fish or dc.creator any sanderson")
    assert parsed is not None
    assert parsed.version == "1.2"


def test_init_parse_debug(caplog: pytest.LogCaptureFixture):
    import logging

    import cql

    with caplog.at_level(logging.INFO, "CQLLexer"):
        _ = cql.parse(
            "dc.title any fish or dc.creator any sanderson", debug_show_lexerinfo=True
        )
    assert all(record.name == "CQLLexer" for record in caplog.records)
    assert all(record.funcName == "lex" for record in caplog.records)
    caplog.clear()

    with caplog.at_level(logging.DEBUG, "CQLParser"):
        _ = cql.parse(
            "dc.title any fish or dc.creator any sanderson", debug_show_parserinfo=True
        )
    assert all(record.name == "CQLParser" for record in caplog.records)
    assert {record.funcName for record in caplog.records} == {"yacc", "lr_parse_table"}
    assert {record.levelname for record in caplog.records} == {
        "INFO",
        "DEBUG",
        "WARNING",
    }
    caplog.clear()

    with caplog.at_level(logging.DEBUG, "CQLParserSteps"):
        _ = cql.parse(
            "dc.title any fish or dc.creator any sanderson", debug_parsing=True
        )
    assert all(record.name == "CQLParserSteps" for record in caplog.records)
    assert {record.funcName for record in caplog.records} == {"parse"}
    assert {record.levelname for record in caplog.records} == {"INFO", "DEBUG"}
    caplog.clear()


# ---------------------------------------------------------------------------
