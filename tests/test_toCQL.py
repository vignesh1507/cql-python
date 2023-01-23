import pytest

from cql.parser import CQLBoolean
from cql.parser import CQLModifier
from cql.parser import CQLModifierable
from cql.parser import CQLPrefix
from cql.parser import CQLPrefixable
from cql.parser import CQLPrefixedName
from cql.parser import CQLQuery
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


def test_CQLPrefixedName():
    assert CQLPrefixedName("test") == "test"
    assert "test" == CQLPrefixedName("test")
    assert CQLPrefixedName("test") != "test2"
    assert "test" != CQLPrefixedName("test2")
    assert CQLPrefixedName("test") == CQLPrefixedName("test")
    assert CQLPrefixedName("test") != CQLPrefixedName("test2")

    assert CQLPrefixedName("test") != 1
    assert CQLPrefixedName("test") != 1.2
    assert CQLPrefixedName("test") != ["test"]
    assert CQLPrefixedName("test") != list("test")

    assert CQLPrefixedName("test").name == "test"
    assert CQLPrefixedName("test").prefix is None
    assert CQLPrefixedName("test").basename == "test"

    assert CQLPrefixedName("abc.def").name == "abc.def"
    assert CQLPrefixedName("abc.def").prefix == "abc"
    assert CQLPrefixedName("abc.def").basename == "def"


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


def test_CQLSearchClause():
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

    obj = CQLSearchClause("fish", "dc.title", CQLRelation("any"))
    objcql = obj.toCQL()
    objp = CQLPrefix("http://deepcustard.org/", "dc")
    objpcql = objp.toCQL()
    obj.add_prefix(objp)
    assert obj.toCQL() == f"{objpcql} {objcql}"
    assert obj.toCQL() == '> dc = "http://deepcustard.org/" dc.title any fish'


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

    obj = CQLTriple(
        left=CQLTriple(
            left=CQLSearchClause("sanderson", "dc.creator", CQLRelation("any")),
            operator=CQLBoolean("and"),
            right=CQLSearchClause("id:1234567", "dc.identifier", CQLRelation("=")),
        ),
        operator=CQLBoolean("or"),
        right=CQLSearchClause("fish", "dc.title", CQLRelation("any")),
    )
    assert (
        obj.toCQL()
        == "(dc.creator any sanderson and dc.identifier = id:1234567) or dc.title any fish"
    )


def test_CQLQuery():
    obj = CQLTriple(
        left=CQLSearchClause("fish", "dc.title", CQLRelation("any")),
        operator=CQLBoolean("or"),
        right=CQLSearchClause("sanderson", "dc.creator", CQLRelation("any")),
    )
    objq = CQLQuery(obj)
    assert objq.version == "1.2"
    assert objq.root == obj
    assert obj.toCQL() == objq.toCQL()

    obj = CQLSearchClause("fish", "title", relation="any")
    objq = CQLQuery(obj, version="1.1")
    assert objq.version == "1.1"
    assert objq.root == obj
    assert obj.toCQL() == objq.toCQL()


# ---------------------------------------------------------------------------


def test___str__():
    obj = CQLModifier("rel.algorithm", "=", "cor")
    assert obj.toCQL() == str(obj)

    obj = CQLModifierable([CQLModifier("rel.algorithm", "=", "cor")])
    assert obj.toCQL() == str(obj)

    obj = CQLRelation(
        "any", [CQLModifier("relevant"), CQLModifier("rel.algorithm", "=", "cor")]
    )
    assert obj.toCQL() == str(obj)

    obj = CQLBoolean(
        "prox", [CQLModifier("unit", "=", "word"), CQLModifier("distance", ">", "3")]
    )
    assert obj.toCQL() == str(obj)

    obj = CQLPrefix("http://deepcustard.org/", "dc")
    assert obj.toCQL() == str(obj)

    obj = CQLPrefixable()
    obj.add_prefix(CQLPrefix("http://deepcustard.org/", "dc"))
    assert obj.toCQL() == str(obj)

    obj = CQLSortSpec("dc.title", [CQLModifier("sort.descending")])
    assert obj.toCQL() == str(obj)

    obj = CQLSortable()
    obj.add_sortSpecs(
        [
            CQLSortSpec("dc.date", [CQLModifier("sort.descending")]),
            CQLSortSpec("dc.title", [CQLModifier("sort.ascending")]),
        ]
    )
    assert obj.toCQL() == str(obj)

    obj = CQLSearchClause("fish", "title", relation="any")
    assert obj.toCQL() == str(obj)

    obj = CQLTriple(
        left=CQLSearchClause("fish", "dc.title", CQLRelation("any")),
        operator=CQLBoolean("or"),
        right=CQLTriple(
            left=CQLSearchClause("sanderson", "dc.creator", CQLRelation("any")),
            operator=CQLBoolean("and"),
            right=CQLSearchClause("id:1234567", "dc.identifier", CQLRelation("=")),
        ),
    )
    assert obj.toCQL() == str(obj)


def test___repr__():
    obj = CQLModifier("rel.algorithm", "=", "cor")
    assert repr(obj) == f"CQLModifier[{obj.toCQL()}]"

    obj = CQLModifierable([CQLModifier("rel.algorithm", "=", "cor")])
    assert repr(obj) == f"CQLModifierable[{obj.toCQL()}]"

    obj = CQLRelation(
        "any", [CQLModifier("relevant"), CQLModifier("rel.algorithm", "=", "cor")]
    )
    assert repr(obj) == f"CQLRelation[{obj.toCQL()}]"

    obj = CQLBoolean(
        "prox", [CQLModifier("unit", "=", "word"), CQLModifier("distance", ">", "3")]
    )
    assert repr(obj) == f"CQLBoolean[{obj.toCQL()}]"

    obj = CQLPrefix("http://deepcustard.org/", "dc")
    assert repr(obj) == f"CQLPrefix[{obj.toCQL()}]"

    obj = CQLPrefixable()
    obj.add_prefix(CQLPrefix("http://deepcustard.org/", "dc"))
    assert repr(obj) == f"CQLPrefixable[{obj.toCQL()}]"

    obj = CQLSortSpec("dc.title", [CQLModifier("sort.descending")])
    assert repr(obj) == f"CQLSortSpec[{obj.toCQL()}]"

    obj = CQLSortable()
    obj.add_sortSpecs(
        [
            CQLSortSpec("dc.date", [CQLModifier("sort.descending")]),
            CQLSortSpec("dc.title", [CQLModifier("sort.ascending")]),
        ]
    )
    assert repr(obj) == f"CQLSortable[{obj.toCQL()}]"

    obj = CQLSearchClause("fish", "title", relation="any")
    assert repr(obj) == f"CQLSearchClause[{obj.toCQL()}]"

    obj = CQLTriple(
        left=CQLSearchClause("fish", "dc.title", CQLRelation("any")),
        operator=CQLBoolean("or"),
        right=CQLTriple(
            left=CQLSearchClause("sanderson", "dc.creator", CQLRelation("any")),
            operator=CQLBoolean("and"),
            right=CQLSearchClause("id:1234567", "dc.identifier", CQLRelation("=")),
        ),
    )
    assert repr(obj) == f"CQLTriple[{obj.toCQL()}]"


# ---------------------------------------------------------------------------
