import pytest

from cql.parser import CQLBoolean
from cql.parser import CQLModifier
from cql.parser import CQLPrefix
from cql.parser import CQLRelation
from cql.parser import CQLSearchClause
from cql.parser import CQLSortable
from cql.parser import CQLSortSpec
from cql.parser import CQLTriple
from cql.parser import escape

# ---------------------------------------------------------------------------


def test_escape():
    assert escape("") == '""'
    assert escape("fish") == "fish"
    assert escape("dc.title") == "dc.title"
    assert escape("fish and sun") == '"fish and sun"'
    assert escape("titl'ed") == "titl'ed"
    assert escape('titl"e"d') == '"titl\\"e\\"d"'
    assert escape("<") == '"<"'
    assert escape(" ") == '" "'
    assert escape(">") == '">"'
    assert escape("=") == '"="'
    assert escape("/") == '"/"'
    assert escape("(") == '"("'
    assert escape(")") == '")"'


# ---------------------------------------------------------------------------


def test_CQLModifier():
    obj = CQLModifier("relevant")
    assert obj.toCQL() == "/relevant"

    obj = CQLModifier("cql.string")
    assert obj.toCQL() == "/cql.string"

    obj = CQLModifier("rel.algorithm", "=", "cor")
    assert obj.toCQL() == "/rel.algorithm=cor"


def test_CQLRelation():
    obj = CQLRelation("any")
    assert obj.toCQL() == "any"

    obj = CQLRelation("any", [CQLModifier("relevant")])
    assert obj.toCQL() == "any/relevant"

    obj = CQLRelation(
        "any", [CQLModifier("relevant"), CQLModifier("rel.algorithm", "=", "cor")]
    )
    assert obj.toCQL() == "any/relevant/rel.algorithm=cor"


def test_CQLBoolean():
    obj = CQLBoolean("and")
    assert obj.toCQL() == "and"
    obj = CQLBoolean("AND")
    assert obj.toCQL() == "AND"

    obj = CQLBoolean("or", [CQLModifier("rel.combine", "=", "sum")])
    assert obj.toCQL() == "or/rel.combine=sum"
    obj = CQLBoolean(
        "prox", [CQLModifier("unit", "=", "word"), CQLModifier("distance", ">", "3")]
    )
    assert obj.toCQL() == "prox/unit=word/distance>3"


def test_CQLPrefix():
    obj = CQLPrefix("http://deepcustard.org/")
    assert obj.toCQL() == '> "http://deepcustard.org/"'

    obj = CQLPrefix("http://deepcustard.org/", "dc")
    assert obj.toCQL() == '> dc = "http://deepcustard.org/"'


def test_CQLSortSpec():
    obj = CQLSortSpec("dc.title")
    assert obj.toCQL() == "sortBy dc.title"

    obj = CQLSortSpec("dc.title", [CQLModifier("sort.descending")])
    assert obj.toCQL() == "sortBy dc.title/sort.descending"


def test_CQLSortable():
    obj = CQLSortable()
    obj.add_sortSpecs([CQLSortSpec("dc.title")])
    assert obj.toCQL() == "sortBy dc.title"

    obj = CQLSortable()
    obj.add_sortSpecs(
        [
            CQLSortSpec("dc.date", [CQLModifier("sort.descending")]),
            CQLSortSpec("dc.title", [CQLModifier("sort.ascending")]),
        ]
    )
    assert obj.toCQL() == "sortBy dc.date/sort.descending dc.title/sort.ascending"


def test_CQLClause():
    obj = CQLSearchClause("fish")
    assert obj.toCQL() == "fish"

    obj = CQLSearchClause("squirrels fish")
    assert obj.toCQL() == '"squirrels fish"'

    obj = CQLSearchClause("")
    assert obj.toCQL() == '""'

    obj = CQLSearchClause("fish", "title", CQLRelation("any"))
    assert obj.toCQL() == "title any fish"

    obj = CQLSearchClause("fish", "dc.title", CQLRelation("any"))
    assert obj.toCQL() == "dc.title any fish"

    obj = CQLSearchClause("fish", "title", relation="any")
    assert isinstance(obj.relation, CQLRelation)
    assert obj.toCQL() == "title any fish"


def test_CQLTriple():
    obj = CQLTriple(
        left=CQLSearchClause("fish", "dc.title", CQLRelation("any")),
        operator=CQLBoolean("or"),
        right=CQLSearchClause("sanderson", "dc.creator", CQLRelation("any")),
    )
    assert obj.toCQL() == "dc.title any fish or dc.creator any sanderson"

    obj = CQLTriple(
        left=CQLSearchClause("fish", "dc.title", CQLRelation("any")),
        operator=CQLBoolean("or"),
        right=CQLTriple(
            left=CQLSearchClause("sanderson", "dc.creator", CQLRelation("any")),
            operator=CQLBoolean("and"),
            right=CQLSearchClause("id:1234567", "dc.identifier", CQLRelation("=")),
        ),
    )
    assert (
        obj.toCQL()
        == "dc.title any fish or (dc.creator any sanderson and dc.identifier = id:1234567)"
    )


# ---------------------------------------------------------------------------
