import xml.etree.ElementTree as ET

import pytest

# from cql.parser import escape
from cql.parser import CQLModifier
from cql.parser import CQLModifierable

# from cql.parser import CQLRelation
# from cql.parser import CQLBoolean
# from cql.parser import CQLPrefix
# from cql.parser import CQLSortSpec
# from cql.parser import CQLSortable
# from cql.parser import CQLClause
# from cql.parser import CQLTriple


# ---------------------------------------------------------------------------


def xmlstr(xml: ET.Element) -> str:
    return ET.tostring(xml, encoding="unicode")


# def test_CQLModifierable():
#     obj = CQLModifierable([CQLModifier("test")])
#     assert xmlstr(obj.toXCQL()) == "<modifiers><modifier>test</modifier></modifiers>"


# ---------------------------------------------------------------------------
