"""Test cases according to examples on the official CQL page:
http://www.loc.gov/standards/sru/cql/spec.html"""

import pytest

from cql.parser import CQLParser
from cql.parser import CQLBoolean
from cql.parser import CQLModifier
from cql.parser import CQLTriple
from cql.parser import CQLClause
from cql.parser import CQLPrefix
from cql.parser import CQLPrefixable
from cql.parser import CQLQuery
from cql.parser import CQLSortable
from cql.parser import CQLSortSpec
from cql.parser import CQLParseError
from cql.parser import CQLPrefixedName


# ---------------------------------------------------------------------------


def test_CQLPrefixedName():
    for s in ("", "abc", "author"):
        obj = CQLPrefixedName(s)
        assert obj.name == s
        assert str(obj) == s
        assert obj == s

        assert obj.prefix is None
        assert obj.basename == s

    obj = CQLPrefixedName("dc.author")
    assert obj.name == "dc.author"
    assert obj == "dc.author"
    assert obj.prefix == "dc"
    assert obj.basename == "author"

    obj = CQLPrefixedName("other.dc.author")
    assert obj.name == "other.dc.author"
    assert obj.prefix == "other"
    assert obj.basename == "dc.author"

    # TODO: ".invalid" / "invalid."


# ---------------------------------------------------------------------------


def test_parser_CQLQuery(parser: CQLParser):
    query = "dc.title any fish"
    parsed: CQLQuery = parser.run(query)
    assert parsed is not None
    assert isinstance(parsed.root, CQLClause)
    assert parsed.root.index == "dc.title"
    assert parsed.root.term == "fish"
    assert parsed.root.relation.comparitor == "any"
    assert parsed.root.relation.modifiers is None

    query = "dc.title any fish or dc.creator any sanderson"
    parsed: CQLQuery = parser.run(query)
    assert parsed is not None
    assert isinstance(parsed.root, CQLTriple)

    bool_op = parsed.root.operator
    assert isinstance(bool_op, CQLBoolean)
    assert bool_op.value.lower() == "or"
    assert bool_op.modifiers is None

    left = parsed.root.left
    assert isinstance(left, CQLClause)
    assert left.toCQL() == "dc.title any fish"
    assert left.index == "dc.title"
    assert left.term == "fish"
    assert left.relation.comparitor == "any"
    assert left.relation.modifiers is None

    right = parsed.root.right
    assert isinstance(right, CQLClause)
    assert right.toCQL() == "dc.creator any sanderson"
    assert right.index == "dc.creator"
    assert right.term == "sanderson"
    assert right.relation.comparitor == "any"
    assert right.relation.modifiers is None

    query = "dc.title any fish sortBy dc.date/sort.ascending"
    parsed: CQLQuery = parser.run(query)
    assert parsed is not None
    assert isinstance(parsed.root, CQLClause)
    assert isinstance(parsed.root, CQLSortable)
    assert parsed.root.index == "dc.title"
    assert parsed.root.term == "fish"
    assert parsed.root.relation.comparitor == "any"
    assert parsed.root.relation.modifiers is None
    assert parsed.root.sortSpecs is not None
    assert len(parsed.root.sortSpecs) == 1
    sortSpec: CQLSortSpec = parsed.root.sortSpecs[0]
    assert isinstance(sortSpec, CQLSortSpec)
    assert sortSpec.index == "dc.date"
    assert isinstance(sortSpec.index, CQLPrefixedName)
    assert sortSpec.index.prefix == "dc"
    assert sortSpec.modifiers is not None
    assert len(sortSpec.modifiers) == 1
    modifier: CQLModifier = sortSpec.modifiers[0]
    assert isinstance(modifier, CQLModifier)
    assert modifier.name == "sort.ascending"
    assert isinstance(modifier.name, CQLPrefixedName)
    assert modifier.name.prefix == "sort"

    query = '> dc = "info:srw/context-sets/1/dc-v1.1" dc.title any fish'
    parsed: CQLQuery = parser.run(query)
    assert parsed is not None
    assert isinstance(parsed.root, CQLClause)
    assert isinstance(parsed.root, CQLPrefixable)
    assert parsed.root.index == "dc.title"
    assert parsed.root.term == "fish"
    assert parsed.root.relation.comparitor == "any"
    assert parsed.root.relation.modifiers is None
    assert parsed.root.prefixes is not None
    assert len(parsed.root.prefixes) == 1
    prefix = parsed.root.prefixes[0]
    assert isinstance(prefix, CQLPrefix)
    assert prefix.uri == "info:srw/context-sets/1/dc-v1.1"
    assert prefix.prefix == "dc"
    assert prefix.toCQL() == '> dc = "info:srw/context-sets/1/dc-v1.1"'


def test_parser_SearchClause(parser: CQLParser):
    query = "dc.title any fish"
    parsed: CQLQuery = parser.run(query)
    assert parsed is not None
    assert isinstance(parsed.root, CQLClause)
    assert parsed.root.index == "dc.title"
    assert parsed.root.term == "fish"
    assert parsed.root.relation.comparitor == "any"
    assert parsed.root.relation.modifiers is None

    query = "fish"
    parsed: CQLQuery = parser.run(query)
    assert parsed is not None
    assert isinstance(parsed.root, CQLClause)
    assert parsed.root.term == "fish"
    assert parsed.root.index is None
    assert parsed.root.relation is None

    query = "fish"
    parsed: CQLQuery = parser.run(query)
    assert parsed.version == "1.2"
    parsed.setServerDefaults()
    assert parsed.root.index == "cql.serverChoice"
    assert parsed.root.relation.comparitor == "="
    assert parsed.root.relation.modifiers is None

    query = "fish"
    parsed: CQLQuery = parser.run(query)
    parsed.version = "1.1"
    parsed.setServerDefaults()
    assert parsed.root.index == "cql.serverChoice"
    assert parsed.root.relation.comparitor == "scr"
    assert parsed.root.relation.modifiers is None

    query = "cql.serverChoice = fish"
    parsed: CQLQuery = parser.run(query)
    assert parsed is not None
    assert isinstance(parsed.root, CQLClause)
    assert parsed.root.term == "fish"
    assert parsed.root.index == "cql.serverChoice"
    assert parsed.root.relation.comparitor == "="
    assert parsed.root.relation.modifiers is None


def test_parser_SearchClause11(parser11: CQLParser):
    query = "dc.title any fish"
    parsed: CQLQuery = parser11.run(query)
    assert parsed is not None
    assert isinstance(parsed.root, CQLClause)
    assert parsed.root.index == "dc.title"
    assert parsed.root.term == "fish"
    assert parsed.root.relation.comparitor == "any"
    assert parsed.root.relation.modifiers is None

    query = "fish"
    parsed: CQLQuery = parser11.run(query)
    assert parsed is not None
    assert isinstance(parsed.root, CQLClause)
    assert parsed.root.term == "fish"
    assert parsed.root.index is None
    assert parsed.root.relation is None

    query = "fish"
    parsed: CQLQuery = parser11.run(query)
    assert parsed.version != "1.2"
    parsed.version = "1.2"
    parsed.setServerDefaults()
    assert parsed.root.index == "cql.serverChoice"
    assert parsed.root.relation.comparitor == "="
    assert parsed.root.relation.modifiers is None

    query = "fish"
    parsed: CQLQuery = parser11.run(query)
    assert parsed.version == "1.1"
    parsed.setServerDefaults()
    assert parsed.root.index == "cql.serverChoice"
    assert parsed.root.relation.comparitor == "scr"
    assert parsed.root.relation.modifiers is None

    query = "cql.serverChoice = fish"
    parsed: CQLQuery = parser11.run(query)
    assert parsed is not None
    assert isinstance(parsed.root, CQLClause)
    assert parsed.root.term == "fish"
    assert parsed.root.index == "cql.serverChoice"
    assert parsed.root.relation.comparitor == "="
    assert parsed.root.relation.modifiers is None


def test_parser_SearchClause12(parser12: CQLParser):
    query = "dc.title any fish"
    parsed: CQLQuery = parser12.run(query)
    assert parsed is not None
    assert isinstance(parsed.root, CQLClause)
    assert parsed.root.index == "dc.title"
    assert parsed.root.term == "fish"
    assert parsed.root.relation.comparitor == "any"
    assert parsed.root.relation.modifiers is None

    query = "fish"
    parsed: CQLQuery = parser12.run(query)
    assert parsed is not None
    assert isinstance(parsed.root, CQLClause)
    assert parsed.root.term == "fish"
    assert parsed.root.index is None
    assert parsed.root.relation is None

    query = "fish"
    parsed: CQLQuery = parser12.run(query)
    assert parsed.version == "1.2"
    parsed.setServerDefaults()
    assert parsed.root.index == "cql.serverChoice"
    assert parsed.root.relation.comparitor == "="
    assert parsed.root.relation.modifiers is None

    query = "fish"
    parsed: CQLQuery = parser12.run(query)
    assert parsed.version != "1.1"
    parsed.version = "1.1"
    parsed.setServerDefaults()
    assert parsed.root.index == "cql.serverChoice"
    assert parsed.root.relation.comparitor == "scr"
    assert parsed.root.relation.modifiers is None

    query = "cql.serverChoice = fish"
    parsed: CQLQuery = parser12.run(query)
    assert parsed is not None
    assert isinstance(parsed.root, CQLClause)
    assert parsed.root.term == "fish"
    assert parsed.root.index == "cql.serverChoice"
    assert parsed.root.relation.comparitor == "="
    assert parsed.root.relation.modifiers is None


def test_parser_SearchTerm(parser: CQLParser):
    query = '"fish"'
    parsed: CQLQuery = parser.run(query)
    assert isinstance(parsed.root, CQLClause)
    assert parsed.root.term == "fish"

    query = "fish"
    parsed: CQLQuery = parser.run(query)
    assert isinstance(parsed.root, CQLClause)
    assert parsed.root.term == "fish"

    query = '"squirrels fish"'
    parsed: CQLQuery = parser.run(query)
    assert isinstance(parsed.root, CQLClause)
    assert parsed.root.term == "squirrels fish"

    query = '""'
    parsed: CQLQuery = parser.run(query)
    assert isinstance(parsed.root, CQLClause)
    assert parsed.root.term == ""


def test_parser_IndexName(parser: CQLParser):
    query = "title any fish"
    parsed: CQLQuery = parser.run(query)
    assert isinstance(parsed.root.index, CQLPrefixedName)
    assert parsed.root.index == "title"

    query = "dc.title any fish"
    parsed: CQLQuery = parser.run(query)
    assert isinstance(parsed.root.index, CQLPrefixedName)
    assert parsed.root.index == "dc.title"
    assert parsed.root.index.prefix == "dc"

    # TODO: add server choice prefix


def test_parser_Relation(parser: CQLParser):
    query = "dc.title any fish"
    parsed: CQLQuery = parser.run(query)
    assert parsed is not None
    assert isinstance(parsed.root, CQLClause)
    assert parsed.root.index == "dc.title"
    assert parsed.root.term == "fish"
    assert parsed.root.relation.comparitor == "any"
    assert isinstance(parsed.root.relation.comparitor, CQLPrefixedName)
    assert parsed.root.relation.modifiers is None

    query = "dc.title cql.any fish"
    parsed: CQLQuery = parser.run(query)
    assert parsed is not None
    assert isinstance(parsed.root, CQLClause)
    assert parsed.root.index == "dc.title"
    assert parsed.root.term == "fish"
    assert parsed.root.relation.comparitor == "cql.any"
    assert isinstance(parsed.root.relation.comparitor, CQLPrefixedName)
    assert parsed.root.relation.modifiers is None


def test_parser_RelationModifiers(parser: CQLParser):
    query = "dc.title any/relevant fish"
    parsed: CQLQuery = parser.run(query)
    assert parsed is not None
    assert isinstance(parsed.root, CQLClause)
    assert parsed.root.index == "dc.title"
    assert parsed.root.term == "fish"
    assert parsed.root.relation.comparitor == "any"
    assert parsed.root.relation.modifiers is not None
    assert len(parsed.root.relation.modifiers) == 1
    modifier: CQLModifier = parsed.root.relation.modifiers[0]
    assert modifier.name == "relevant"
    assert modifier.value is None
    assert modifier.comparitor is None

    query = "dc.title any/ relevant /cql.string fish"
    parsed: CQLQuery = parser.run(query)
    assert parsed is not None
    assert isinstance(parsed.root, CQLClause)
    assert parsed.root.index == "dc.title"
    assert parsed.root.term == "fish"
    assert parsed.root.relation.comparitor == "any"
    assert parsed.root.relation.modifiers is not None
    assert len(parsed.root.relation.modifiers) == 2
    modifier: CQLModifier = parsed.root.relation.modifiers[0]
    assert modifier.name == "relevant"
    assert modifier.value is None
    assert modifier.comparitor is None
    modifier: CQLModifier = parsed.root.relation.modifiers[1]
    assert modifier.name == "cql.string"
    assert modifier.value is None
    assert modifier.comparitor is None

    query = "dc.title any/rel.algorithm=cori fish"
    parsed: CQLQuery = parser.run(query)
    assert parsed is not None
    assert isinstance(parsed.root, CQLClause)
    assert parsed.root.index == "dc.title"
    assert parsed.root.term == "fish"
    assert parsed.root.relation.comparitor == "any"
    assert parsed.root.relation.modifiers is not None
    assert len(parsed.root.relation.modifiers) == 1
    modifier: CQLModifier = parsed.root.relation.modifiers[0]
    assert modifier.name == "rel.algorithm"
    assert modifier.value == "cori"
    assert modifier.comparitor == "="


def test_parser_BooleanOperators(parser: CQLParser):
    query = "dc.title any fish or dc.creator any sanderson"
    parsed: CQLTriple = parser.run(query)
    assert parsed is not None
    assert isinstance(parsed.root, CQLTriple)
    left: CQLClause = parsed.root.left
    assert left.index == "dc.title"
    assert left.relation.comparitor == "any"
    assert left.relation.modifiers is None
    assert left.term == "fish"
    right: CQLClause = parsed.root.right
    assert right.index == "dc.creator"
    assert right.relation.comparitor == "any"
    assert right.relation.modifiers is None
    assert right.term == "sanderson"

    bool_op: CQLBoolean = parsed.root.operator
    assert bool_op.value.lower() == "or"
    assert bool_op.modifiers is None

    query = 'dc.title any fish or (dc.creator any sanderson and dc.identifier = "id:1234567")'
    parsed: CQLTriple = parser.run(query)
    assert parsed is not None
    assert isinstance(parsed.root, CQLTriple)
    left: CQLClause = parsed.root.left
    assert left.index == "dc.title"
    assert left.relation.comparitor == "any"
    assert left.relation.modifiers is None
    assert left.term == "fish"

    bool_op: CQLBoolean = parsed.root.operator
    assert bool_op.value.lower() == "or"

    right_outer: CQLTriple = parsed.root.right
    assert isinstance(right_outer, CQLTriple)

    bool_op: CQLBoolean = right_outer.operator
    assert bool_op.value.lower() == "and"

    left: CQLClause = right_outer.left
    assert left.index == "dc.creator"
    assert left.relation.comparitor == "any"
    assert left.relation.modifiers is None
    assert left.term == "sanderson"

    right: CQLClause = right_outer.right
    assert right.index == "dc.identifier"
    assert right.relation.comparitor == "="
    assert right.relation.modifiers is None
    assert right.term == "id:1234567"


def test_parser_BooleanModifiers(parser: CQLParser):
    query = "dc.title any fish or/rel.combine=sum dc.creator any sanderson"
    parsed: CQLTriple = parser.run(query)
    assert parsed is not None
    assert isinstance(parsed.root, CQLTriple)
    left: CQLClause = parsed.root.left
    assert left.index == "dc.title"
    assert left.relation.comparitor == "any"
    assert left.relation.modifiers is None
    assert left.term == "fish"
    right: CQLClause = parsed.root.right
    assert right.index == "dc.creator"
    assert right.relation.comparitor == "any"
    assert right.relation.modifiers is None
    assert right.term == "sanderson"
    bool_op: CQLBoolean = parsed.root.operator
    assert bool_op.value.lower() == "or"

    assert bool_op.modifiers is not None
    modifier: CQLModifier = bool_op.modifiers[0]
    assert modifier.name == "rel.combine"
    assert modifier.comparitor == "="
    assert modifier.value == "sum"

    query = "dc.title any fish prox/unit=word/distance>3 dc.title any squirrel"
    parsed: CQLTriple = parser.run(query)
    assert parsed is not None
    assert isinstance(parsed.root, CQLTriple)
    left: CQLClause = parsed.root.left
    assert left.index == "dc.title"
    assert left.relation.comparitor == "any"
    assert left.relation.modifiers is None
    assert left.term == "fish"
    right: CQLClause = parsed.root.right
    assert right.index == "dc.title"
    assert right.relation.comparitor == "any"
    assert right.relation.modifiers is None
    assert right.term == "squirrel"
    bool_op: CQLBoolean = parsed.root.operator
    assert bool_op.value.lower() == "prox"

    assert len(bool_op.modifiers) == 2
    modifier: CQLModifier = bool_op.modifiers[0]
    assert modifier.name == "unit"
    assert modifier.comparitor == "="
    assert modifier.value == "word"
    modifier: CQLModifier = bool_op.modifiers[1]
    assert modifier.name == "distance"
    assert modifier.comparitor == ">"
    assert modifier.value == "3"


def test_parser_Sorting(parser: CQLParser):
    query = '"cat" sortBy dc.title'
    parsed: CQLQuery = parser.run(query)
    assert parsed is not None
    assert isinstance(parsed.root, CQLClause)
    assert parsed.root.term == "cat"
    assert parsed.root.sortSpecs
    sortKey = parsed.root.sortSpecs[0]
    assert sortKey.index == "dc.title"
    assert sortKey.modifiers is None

    query = '"dinosaur" sortBy dc.date/sort.descending dc.title/sort.ascending'
    parsed: CQLQuery = parser.run(query)
    assert parsed is not None
    assert isinstance(parsed.root, CQLClause)
    assert parsed.root.term == "dinosaur"
    assert len(parsed.root.sortSpecs) == 2
    sortKey = parsed.root.sortSpecs[0]
    assert sortKey.index == "dc.date"
    assert len(sortKey.modifiers) == 1
    assert sortKey.modifiers[0].name == "sort.descending"
    assert sortKey.modifiers[0].value is None
    sortKey = parsed.root.sortSpecs[1]
    assert sortKey.index == "dc.title"
    assert len(sortKey.modifiers) == 1
    assert sortKey.modifiers[0].name == "sort.ascending"
    assert sortKey.modifiers[0].value is None


def test_parser_PrefixAssignment(parser: CQLParser):
    query = """> dc = "http://deepcustard.org/" dc.custardDepth > 10"""
    parsed: CQLQuery = parser.run(query)
    assert parsed is not None
    assert isinstance(parsed.root, CQLClause)
    assert parsed.root.index == "dc.custardDepth"
    assert parsed.root.relation.comparitor == ">"
    assert parsed.root.relation.modifiers is None
    assert parsed.root.term == "10"
    assert parsed.root.prefixes
    prefix: CQLPrefix = parsed.root.prefixes[0]
    assert prefix.prefix == "dc"
    assert prefix.uri == "http://deepcustard.org/"

    query = """> "http://deepcustard.org/" custardDepth > 10 """
    parsed: CQLQuery = parser.run(query)
    assert parsed is not None
    assert isinstance(parsed.root, CQLClause)
    assert parsed.root.index == "custardDepth"
    assert parsed.root.relation.comparitor == ">"
    assert parsed.root.relation.modifiers is None
    assert parsed.root.term == "10"
    assert parsed.root.prefixes
    prefix: CQLPrefix = parsed.root.prefixes[0]
    assert prefix.uri == "http://deepcustard.org/"
    # TODO: do we want to have this as output?
    assert prefix.prefix is None
    parsed.setServerDefaults()
    assert prefix.prefix == "cql.serverChoice"


def test_parser_CaseInsensitive(parser11: CQLParser):
    query = "dC.tiTlE any fish"
    parsed: CQLClause = parser11.run(query)
    assert parsed is not None
    assert isinstance(parsed.root, CQLClause)
    assert parsed.root.term == "fish"
    assert parsed.root.relation.comparitor == "any"
    assert parsed.root.relation.modifiers is None
    assert parsed.root.index == "dC.tiTlE"

    # NOTE: not supported sortby
    query = "dc.TitlE Any/rEl.algOriThm=cori fish soRtbY Dc.TitlE "
    with pytest.raises(CQLParseError):
        parser11.run(query)


def test_parser_CaseInsensitive2(parser12: CQLParser):
    query = "dC.tiTlE any fish"
    parsed: CQLClause = parser12.run(query)
    assert parsed is not None
    assert isinstance(parsed.root, CQLClause)
    assert parsed.root.term == "fish"
    assert parsed.root.relation.comparitor == "any"
    assert parsed.root.relation.modifiers is None
    assert parsed.root.index == "dC.tiTlE"

    query = "dc.TitlE Any/rEl.algOriThm=cori fish soRtbY Dc.TitlE "
    parsed: CQLClause = parser12.run(query)
    assert parsed is not None
    assert isinstance(parsed.root, CQLClause)
    assert parsed.root.term == "fish"
    assert parsed.root.index == "dc.TitlE"
    assert parsed.root.relation.comparitor == "Any"
    assert parsed.root.relation.modifiers
    modifier = parsed.root.relation.modifiers[0]
    assert modifier.name == "rEl.algOriThm"
    assert modifier.comparitor == "="
    assert modifier.value == "cori"
    assert parsed.root.sortSpecs
    sortKey = parsed.root.sortSpecs[0]
    assert sortKey.index == "Dc.TitlE"
    assert sortKey.modifiers is None


# ---------------------------------------------------------------------------


def test_parser_SearchTerm_full(parser: CQLParser):
    query = '"fish"'
    parsed: CQLQuery = parser.run(query)
    assert parsed is not None
    assert isinstance(parsed.root, CQLClause)
    assert parsed.root.term == "fish"
    assert parsed.root.index is None
    assert parsed.root.relation is None

    query = "fish"
    parsed: CQLQuery = parser.run(query)
    assert parsed is not None
    assert isinstance(parsed.root, CQLClause)
    assert parsed.root.term == "fish"
    assert parsed.root.index is None
    assert parsed.root.relation is None

    query = '"squirrels fish"'
    parsed: CQLQuery = parser.run(query)
    assert parsed is not None
    assert isinstance(parsed.root, CQLClause)
    assert parsed.root.term == "squirrels fish"
    assert parsed.root.index is None
    assert parsed.root.relation is None

    query = '""'
    parsed: CQLQuery = parser.run(query)
    assert parsed is not None
    assert isinstance(parsed.root, CQLClause)
    assert parsed.root.term == ""
    assert parsed.root.index is None
    assert parsed.root.relation is None


def test_parser_IndexName_full(parser: CQLParser):
    query = "title any fish"
    parsed: CQLQuery = parser.run(query)
    assert parsed is not None
    assert isinstance(parsed.root, CQLClause)
    assert parsed.root.index == "title"
    assert isinstance(parsed.root.index, CQLPrefixedName)
    assert parsed.root.index.prefix is None
    assert parsed.root.index.basename == "title"
    assert parsed.root.term == "fish"
    assert parsed.root.relation.comparitor == "any"
    assert parsed.root.relation.modifiers is None

    query = "dc.title any fish"
    parsed: CQLQuery = parser.run(query)
    assert parsed is not None
    assert isinstance(parsed.root, CQLClause)
    assert parsed.root.index == "dc.title"
    assert isinstance(parsed.root.index, CQLPrefixedName)
    assert parsed.root.index.prefix == "dc"
    assert parsed.root.index.basename == "title"
    assert parsed.root.term == "fish"
    assert parsed.root.relation.comparitor == "any"
    assert parsed.root.relation.modifiers is None


# ---------------------------------------------------------------------------
