import os
import os.path
import xml.etree.ElementTree as ET
from itertools import chain
from itertools import repeat
from typing import Tuple
from xml.dom import minidom

import pytest

from cql.parser import CQLParser
from cql.parser import CQLParserError
from cql.parser import CQLQuery

# ---------------------------------------------------------------------------


def xmlstr(xml: ET.Element) -> str:
    # strip namespace
    del xml.attrib["xmlns"]
    xmlstr = ET.tostring(
        xml, encoding="unicode", xml_declaration=False, short_empty_elements=False
    )
    xmlstr = minidom.parseString(xmlstr).toprettyxml(indent="  ")
    xmlstr = xmlstr.split("\n", 1)[1]
    return xmlstr


def load_content(name: str) -> str:
    base_path = os.path.dirname(__file__)
    fname = os.path.join(base_path, name)
    with open(fname, "r") as fp:
        return fp.read()


def get_variants(id: str):
    base_path = os.path.dirname(__file__)

    variants_dir = os.path.join(base_path, id)

    if not os.path.exists(variants_dir):
        raise FileNotFoundError(f"Missing test data folder? '{variants_dir}'")

    with open(os.path.join(variants_dir, "name"), "r") as fp:
        name = fp.read().strip()

    files = os.listdir(variants_dir)
    files = [f for f in files if f != "name"]
    files = [f for f in files if not f.endswith(".disabled")]
    files = sorted({os.path.splitext(f)[0] for f in files})
    files = [f"{id}/{f}" for f in files]

    files = zip(repeat(name), files)

    return files


def get_variants_all():
    base_path = os.path.dirname(__file__)

    ids = os.listdir(base_path)
    ids = [
        f
        for f in ids
        if os.path.isdir(os.path.join(base_path, f)) and len(f) == 2 and f.isdigit()
    ]

    return chain.from_iterable(get_variants(id) for id in ids)


# ---------------------------------------------------------------------------


@pytest.mark.parametrize("type,id", get_variants_all())
def test_cql2xcql(parser: CQLParser, type: str, id: str):
    cql = load_content(f"{id}.cql")
    xcql = load_content(f"{id}.xcql")

    if id == "10/15":
        pytest.skip("TODO: prefix sorting issue")
    elif id == "09/01":
        pytest.skip("TODO: operators vs. term")
    elif id == "12/01":
        pytest.skip("TODO: might be wrong correct answer?")
    elif id == "10/13":
        pytest.skip("TODO: this should not be allowed based on the BNF")
    elif id == "10/16":
        pytest.skip(
            "TODO: investigate this. <prefix> 'dc.title=jaws' should be in parentheses."
        )

    elif id in ("08/02", "09/04"):
        # do not add server default
        parsed: CQLQuery = parser.parse(cql)
        xml = parsed.toXCQL()
        assert xmlstr(xml) == xcql
    elif id in ("09/03",):
        # our pretty print lib does collapse empty elements
        parsed: CQLQuery = parser.parse(cql)
        parsed.setServerDefaults()
        xml = parsed.toXCQL()
        assert xmlstr(xml).replace("<term/>", "<term></term>") == xcql
    elif id in ("06/06", "06/03"):
        # our pretty print lib does escape some strings ...
        parsed: CQLQuery = parser.parse(cql)
        parsed.setServerDefaults()
        xml = parsed.toXCQL()
        assert xmlstr(xml).replace("&quot;", '"') == xcql

    elif type == "FAILURES":
        parsed: CQLQuery = None
        with pytest.raises(CQLParserError) as exc_info:
            parsed = parser.parse(cql)
        assert parsed is None
    elif type == "Sorting" or id in ("05/08",):
        # NOTE: ignore some case folding which we do not automatically
        # is not required / most stuff is case-insensitive (so no changes by us for now)
        parsed: CQLQuery = parser.parse(cql)
        parsed.setServerDefaults()
        xml = parsed.toXCQL()
        assert xmlstr(xml).lower() == xcql.lower()

    else:
        parsed: CQLQuery = parser.parse(cql)
        parsed.setServerDefaults()
        xml = parsed.toXCQL()
        assert xmlstr(xml) == xcql


# ---------------------------------------------------------------------------
