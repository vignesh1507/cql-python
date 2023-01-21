import logging
import xml.etree.ElementTree as ET
from typing import List
from typing import Optional
from typing import Union

import ply.yacc as yacc
from ply.lex import Lexer
from ply.lex import LexToken
from ply.yacc import LRParser
from ply.yacc import YaccProduction
from ply.yacc import YaccSymbol

from .lexer import CQLLexer

LOGGER = logging.getLogger(__name__)


# ---------------------------------------------------------------------------


XCQL_NAMESPACE = "http://www.loc.gov/zing/cql/xcql/"

# see notes at http://www.loc.gov/standards/sru/cql/spec.html#note1
CQL12_DEFAULT_RELATION = "="
CQL11_DEFAULT_RELATION = "scr"
CQL_DEFAULT_INDEX = "cql.serverChoice"


# ---------------------------------------------------------------------------


def escape(val: str) -> str:
    if isinstance(val, CQLPrefixedName):
        val = val.name
    if len(val) == 0:
        return '""'
    if any(c in val for c in (' \t\r\n\f\v<>=/()"')):
        return '"' + val.replace('"', '\\"') + '"'
    return val


# ---------------------------------------------------------------------------


class CQLParseError(Exception):
    pass


# ---------------------------------------------------------------------------


class CQLPrefixedName:
    def __init__(self, name: str):
        self.name = name

    @property
    def prefix(self) -> Optional[str]:
        if "." not in self.name:
            return None
        return self.name.split(".", 1)[0]

    @property
    def basename(self) -> str:
        if "." not in self.name:
            return self.name
        return self.name.split(".", 1)[1]

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return repr(self.name)

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, str):
            return __o == self.name
        if isinstance(__o, CQLPrefixedName):
            return __o.name == self.name
        return False


# ---------------------------------------------------------------------------


class CQLModifier:
    def __init__(self, name: str, comparitor: str = None, value: str = None):
        self.name = (
            CQLPrefixedName(name) if not isinstance(name, CQLPrefixedName) else name
        )
        self.comparitor = comparitor
        self.value = value
        # TODO: check prefix splitting

    def toCQL(self) -> str:
        if self.comparitor is not None:
            return f"/{escape(self.name)}{self.comparitor}{escape(self.value)}"
        return f"/{escape(self.name)}"

    def toXCQL(self) -> ET.Element:
        ele = ET.Element("modifier")
        ET.SubElement(ele, "type").text = str(self.name)
        if self.comparitor is not None and self.value is not None:
            ET.SubElement(ele, "comparison").text = self.comparitor
            ET.SubElement(ele, "value").text = self.value
        return ele

    def __str__(self) -> str:
        return self.toCQL()

    def __repr__(self) -> str:
        return f"CQLModifier[{self.toCQL()}]"


class CQLModifierable:
    def __init__(self, modifiers: List[CQLModifier] = None):
        self.modifiers = modifiers

    def toCQL(self) -> str:
        if not self.modifiers:
            return ""
        return "".join(m.toCQL() for m in self.modifiers)

    def toXCQL(self) -> Optional[ET.Element]:
        if not self.modifiers:
            return None

        ele = ET.Element("modifiers")
        for modifier in self.modifiers:
            ele.append(modifier.toXCQL())
        return ele

    def __str__(self) -> str:
        return self.toCQL()

    def __repr__(self) -> str:
        return f"CQLModifierable[{self.toCQL()}]"


class CQLPrefix:
    def __init__(self, uri: str, prefix: str = None):
        self.prefix = prefix
        self.uri = uri

    def toCQL(self) -> str:
        if self.prefix is None:
            return f"> {escape(self.uri)}"
        return f"> {self.prefix} = {escape(self.uri)}"

    def toXCQL(self) -> ET.Element:
        ele = ET.Element("prefix")
        if self.prefix is not None:
            ET.SubElement(ele, "name").text = str(self.prefix)
        ET.SubElement(ele, "identifier").text = self.uri
        return ele

    def __str__(self) -> str:
        return self.toCQL()

    def __repr__(self) -> str:
        return f"CQLPrefix[{self.toCQL()}]"


class CQLPrefixable:
    def __init__(self):
        super().__init__()
        self.prefixes: List[CQLPrefix] = list()

    def add_prefix(self, prefix: CQLPrefix):
        self.prefixes.append(prefix)

    def toCQL(self) -> str:
        return " ".join(p.toCQL() for p in self.prefixes)

    def toXCQL(self) -> Optional[ET.Element]:
        if not self.prefixes:
            return None

        ele_prefixes = ET.Element("prefixes")
        # sorted(self.prefixes, key=lambda p: (p.prefix, p.uri))
        for prefix in self.prefixes:
            ele_prefixes.append(prefix.toXCQL())
        return ele_prefixes

    def __str__(self) -> str:
        return self.toCQL()

    def __repr__(self) -> str:
        return f"CQLPrefixable[{self.toCQL()}]"


class CQLSortSpec(CQLModifierable):
    def __init__(self, index: str, modifiers: List[str] = None):
        super().__init__(modifiers)
        self.index = (
            CQLPrefixedName(index) if not isinstance(index, CQLPrefixedName) else index
        )

    def toCQL(self):
        return f"sortBy {escape(self.index)}{CQLModifierable.toCQL(self)}"

    def toXCQL(self) -> ET.Element:
        ele = ET.Element("key")
        ET.SubElement(ele, "index").text = str(self.index)
        ele_modifiers = CQLModifierable.toXCQL(self)
        if ele_modifiers:
            ele.append(ele_modifiers)
        return ele

    def __str__(self) -> str:
        return self.toCQL()

    def __repr__(self) -> str:
        return f"CQLSortSpec[{self.toCQL()}]"


class CQLSortable:
    def __init__(self):
        super().__init__()
        self.sortSpecs: List[CQLSortSpec] = list()

    def add_sortSpecs(self, sortSpecs: List[CQLSortSpec]):
        self.sortSpecs = sortSpecs

    def toCQL(self):
        return " ".join(
            ["sortBy"]
            + [
                f"{escape(sortSpec.index)}{CQLModifierable.toCQL(sortSpec)}"
                for sortSpec in self.sortSpecs
            ]
        )

    def toXCQL(self) -> Optional[ET.Element]:
        if not self.sortSpecs:
            return None

        ele_sortKeys = ET.Element("sortKeys")
        for sortSpec in self.sortSpecs:
            ele_sortKeys.append(sortSpec.toXCQL())
        return ele_sortKeys

    def __str__(self) -> str:
        return self.toCQL()

    def __repr__(self) -> str:
        return f"CQLSortable[{self.toCQL()}]"


# ---------------------------------------------------------------------------


class CQLRelation(CQLModifierable):
    def __init__(self, comparitor: str, modifiers: List[CQLModifier] = None):
        super().__init__(modifiers)
        self.comparitor = (
            CQLPrefixedName(comparitor)
            if not isinstance(comparitor, CQLPrefixedName)
            else comparitor
        )

    def toCQL(self) -> str:
        return f"{self.comparitor}{CQLModifierable.toCQL(self)}"

    def toXCQL(self) -> ET.Element:
        ele = ET.Element("relation")
        ET.SubElement(ele, "value").text = str(self.comparitor)

        ele_modifiers = CQLModifierable.toXCQL(self)
        if ele_modifiers:
            ele.append(ele_modifiers)
        return ele

    def __repr__(self) -> str:
        return f"CQLRelation[{self.toCQL()}]"

    def __str__(self) -> str:
        return self.toCQL()


class CQLBoolean(CQLModifierable):
    def __init__(self, value: str, modifiers: List[str] = None):
        super().__init__(modifiers)
        self.value = value

    def toCQL(self) -> str:
        return f"{self.value}{CQLModifierable.toCQL(self)}"

    def toXCQL(self) -> ET.Element:
        ele = ET.Element("boolean")
        ET.SubElement(ele, "value").text = self.value
        ele_modifiers = CQLModifierable.toXCQL(self)
        if ele_modifiers:
            ele.append(ele_modifiers)
        return ele

    def __str__(self) -> str:
        return self.toCQL()

    def __repr__(self) -> str:
        return f"CQLBoolean[{self.toCQL()}]"


class CQLSearchClause(CQLPrefixable, CQLSortable):
    def __init__(self, term: str, index=None, relation: CQLRelation = None):
        super().__init__()
        self.term = term
        if index is not None:
            if not isinstance(index, CQLPrefixedName):
                index = CQLPrefixedName(index)
        self.index = index
        if relation is not None:
            if not isinstance(relation, CQLRelation):
                LOGGER.warning(
                    "Parameter 'relation' is plain string instead of CQLRelation!"
                )
                relation = CQLRelation(relation)
        self.relation = relation

    def toCQL(self) -> str:
        if self.relation is None:
            sc = f"{escape(self.term)}"
        else:
            sc = f"{escape(self.index)} {self.relation.toCQL()} {escape(self.term)}"

        p = CQLPrefixable.toCQL(self)
        if p:
            sc = f"{p} {sc}"

        return sc

    def toXCQL(self) -> ET.Element:
        ele = ET.Element("searchClause")

        ele_prefixes = CQLPrefixable.toXCQL(self)
        if ele_prefixes:
            ele.append(ele_prefixes)

        if self.index is not None and self.relation is not None:
            ET.SubElement(ele, "index").text = str(self.index)
            # ET.SubElement(ele_index, "value").text = str(self.index)
            ele.append(self.relation.toXCQL())
        ET.SubElement(ele, "term").text = self.term

        ele_sortKeys = CQLSortable.toXCQL(self)
        if ele_sortKeys:
            ele.append(ele_sortKeys)

        return ele

    def __str__(self) -> str:
        return self.toCQL()

    def __repr__(self) -> str:
        return f"CQLSearchClause[{self.toCQL()}]"


class CQLTriple(CQLPrefixable, CQLSortable):
    def __init__(
        self,
        left: Union["CQLTriple", CQLSearchClause],
        operator: CQLBoolean,
        right: Union["CQLTriple", CQLSearchClause],
    ):
        super().__init__()
        self.left = left
        self.operator = operator
        self.right = right

    def toCQL(self) -> str:
        left = self.left.toCQL()
        if isinstance(self.left, CQLTriple):
            left = f"({left})"
        right = self.right.toCQL()
        if isinstance(self.right, CQLTriple):
            right = f"({right})"
        return f"{left} {self.operator.toCQL()} {right}"

    def toXCQL(self) -> ET.Element:
        ele = ET.Element("triple")

        ele_prefixes = CQLPrefixable.toXCQL(self)
        if ele_prefixes:
            ele.append(ele_prefixes)

        ele.append(self.operator.toXCQL())
        ET.SubElement(ele, "leftOperand").append(self.left.toXCQL())
        ET.SubElement(ele, "rightOperand").append(self.right.toXCQL())

        ele_sortKeys = CQLSortable.toXCQL(self)
        if ele_sortKeys:
            ele.append(ele_sortKeys)

        return ele

    def __str__(self) -> str:
        return self.toCQL()

    def __repr__(self) -> str:
        return f"CQLTriple[{self.toCQL()}]"


class CQLQuery:
    def __init__(self, root: Union[CQLTriple, CQLSearchClause], version="1.2"):
        self.root = root
        self.version = version

    def setServerDefaults(self, addCQLPrefixes: bool = False, serverPrefix: str = None):
        # iterate over all "empty" fields and set server defaults
        # TODO: also do for prefixes?

        def _setDefaults(obj):
            if isinstance(obj, CQLPrefixable):
                if obj.prefixes:
                    for prefix in obj.prefixes:
                        if prefix.prefix is None:
                            prefix.prefix = CQL_DEFAULT_INDEX

            if isinstance(obj, CQLModifierable):
                if obj.modifiers:
                    for modifier in obj.modifiers:
                        pass

            if isinstance(obj, CQLSortable):
                if obj.sortSpecs:
                    for sortSpec in obj.sortSpecs:
                        _setDefaults(sortSpec)

            if isinstance(obj, CQLTriple):
                _setDefaults(obj.operator)
                _setDefaults(obj.left)
                _setDefaults(obj.right)
            elif isinstance(obj, CQLSearchClause):
                if obj.index is None and obj.relation is None:
                    obj.index = CQL_DEFAULT_INDEX
                    obj.relation = CQLRelation(
                        CQL11_DEFAULT_RELATION
                        if self.version == "1.1"
                        else CQL12_DEFAULT_RELATION
                    )
                _setDefaults(obj.relation)

        _setDefaults(self.root)

    def toCQL(self) -> str:
        return self.root.toCQL()

    def toXCQL(self) -> ET.Element:
        ele: ET.Element = self.root.toXCQL()
        ele.attrib["xmlns"] = XCQL_NAMESPACE
        return ele

    def toXCQLString(self, pretty: bool = False) -> str:
        tree = self.toXCQL()

        xmlstr = ET.tostring(tree, encoding="unicode")

        if pretty:
            # ET.indent() in Python 3.9+
            from xml.dom import minidom

            xmlstr = minidom.parseString(xmlstr).toprettyxml(indent="  ")

        return xmlstr


# ---------------------------------------------------------------------------


class CQLParser:
    def build(self, lexer: Lexer, **kwargs) -> None:
        if lexer is None:
            lexer = CQLLexer()
            lexer.build()
        self.lexer: Lexer = lexer
        self.parser: LRParser = yacc.yacc(module=self, **kwargs)

    def run(self, content: str, **kwargs) -> CQLQuery:
        LOGGER.debug("Input: %s", content)
        result = self.parser.parse(content, lexer=self.lexer.lexer, **kwargs)
        return result


# ---------------------------------------------------------------------------


class CQLParser11(CQLParser):
    start = "cqlQuery"

    tokens = CQLLexer.tokens

    # ---------------------------------------------------

    def p_cqlQuery(self, p: YaccProduction):
        # fmt: off
        """cqlQuery : prefixAssignmentGroup cqlQuery
                    | scopedClause"""
        # fmt: on
        LOGGER.debug("p_cqlQuery: %s -> %s", p.slice[1:], p[1:])
        if len(p) == 3:
            LOGGER.debug("p_cqlQuery (assign prefix): %s <<- %s", p.slice[2], p[1])
            for prefix in p[1]:
                p[2].add_prefix(prefix)
            p[0] = p[2]
        else:
            p[0] = p[1]
        LOGGER.debug("stack@p_cqlQuery: %s", p.stack)
        if len(p.stack) == 1 and p.stack[0].type == "$end":
            p[0] = CQLQuery(p[0], version="1.1")

    def p_prefixAssignmentGroup(self, p: YaccProduction):
        # to have left precedence (not really according to specs? but for cql-java tests)
        # fmt: off
        """prefixAssignmentGroup : prefixAssignmentGroup prefixAssignment
                                 | prefixAssignment"""
        # fmt: on
        LOGGER.debug("p_prefixAssignmentGroup: %s -> %r", p.slice[1:], p[1])
        if len(p) == 2:
            p[0] = list()
            p[0].append(p[1])
        else:
            if not isinstance(p[0], list):
                p[0] = list()
            p[0].extend(p[1])
            p[0].append(p[2])

    def p_prefixAssignment(self, p: YaccProduction):
        # fmt: off
        """prefixAssignment : GT prefix EQ uri
                            | GT uri"""
        # fmt: on
        LOGGER.debug("p_prefixAssignment: %s", p.slice[1:])
        if len(p) == 5:
            p[0] = CQLPrefix(uri=p[4], prefix=p[2])
        else:
            p[0] = CQLPrefix(uri=p[2])

    def p_scopedClause(self, p: YaccProduction):
        # fmt: off
        """scopedClause : scopedClause booleanGroup searchClause
                        | searchClause"""
        # fmt: on
        LOGGER.debug("p_scopedClause: %s -> %s", p.slice[1:], p[1:])
        if len(p) == 4:
            p[0] = CQLTriple(left=p[1], operator=p[2], right=p[3])
        else:
            p[0] = p[1]

    def p_booleanGroup(self, p: YaccProduction):
        # fmt: off
        """booleanGroup : boolean modifierList
                        | boolean"""
        # fmt: on
        LOGGER.debug("p_booleanGroup: %s -> %r", p.slice[1:], p[1])
        if len(p) == 3:
            p[0] = CQLBoolean(p[1], modifiers=p[2])
        else:
            p[0] = CQLBoolean(p[1])

    def p_boolean(self, p: YaccProduction):
        # fmt: off
        """boolean : BOOL_AND
                   | BOOL_OR
                   | BOOL_NOT
                   | BOOL_PROX"""
        # fmt: om
        LOGGER.debug("p_boolean: %s", p.slice[1])
        p[0] = p[1]

    def p_searchClause(self, p: YaccProduction):
        # fmt: off
        """searchClause : LPAREN cqlQuery RPAREN
                        | index relation searchTerm
                        | searchTerm"""
        # fmt: on
        LOGGER.debug("p_searchClause: %s -> %s", p.slice[1:], p[1:])
        if len(p) == 4:
            if p.slice[1].type == "LPAREN" and p.slice[3].type == "RPAREN":
                p[0] = p[2]
            else:
                p[0] = CQLSearchClause(term=p[3], relation=p[2], index=p[1])
        else:
            p[0] = CQLSearchClause(term=p[1])

    def p_relation(self, p: YaccProduction):
        # fmt: off
        """relation : comparitor modifierList
                    | comparitor"""
        # fmt: on
        LOGGER.debug("p_relation: %s -> %r", p.slice[1:], p[1])
        if len(p) == 3:
            p[0] = CQLRelation(p[1], modifiers=p[2])
        else:
            p[0] = CQLRelation(p[1])

    def p_comparitor(self, p: YaccProduction):
        # fmt: off
        """comparitor : comparitorSymbol
                      | namedComparitor"""
        # fmt: on
        LOGGER.debug("p_comparitor: %s -> %r", p.slice[1], p[1])
        p[0] = p[1]

    def p_comparitorSymbol(self, p: YaccProduction):
        # fmt: off
        """comparitorSymbol : EQ
                            | GT
                            | LT
                            | GE
                            | LE
                            | NE
                            | EQUALS"""
        # fmt: on
        LOGGER.debug("p_comparitorSymbol: %s", p.slice[1])
        p[0] = p[1]

    def p_namedComparitor(self, p: YaccProduction):
        """namedComparitor : identifier"""
        LOGGER.debug("p_namedComparitor: %s -> %s", p.slice[1], p[1])
        p[0] = p[1]

    def p_modifierList(self, p: YaccProduction):
        # fmt: off
        """modifierList : modifierList modifier
                        | modifier"""
        # fmt: on
        LOGGER.debug("p_modifierList: %s", p.slice[1:])
        if len(p) == 2:
            p[0] = list()
            p[0].append(p[1])
        else:
            if not isinstance(p[0], list):
                p[0] = list()
            p[0].extend(p[1])
            p[0].append(p[2])

    def p_modifier(self, p: YaccProduction):
        # fmt: off
        """modifier : MODSTART modifierName comparitorSymbol modifierValue
                    | MODSTART modifierName"""
        # fmt: on
        LOGGER.debug("p_modifier: %s", p.slice[1:])
        if len(p) == 5:
            p[0] = CQLModifier(p[2], comparitor=p[3], value=p[4])
        else:
            p[0] = CQLModifier(p[2])

    def p_prefix(self, p: YaccProduction):
        """prefix : term"""
        # LOGGER.debug("p_prefix: %s -> %r", p.slice[1], p[1])
        p[0] = p[1]

    def p_uri(self, p: YaccProduction):
        """uri : term"""
        # LOGGER.debug("p_uri: %s -> %r", p.slice[1], p[1])
        p[0] = p[1]

    def p_modifierName(self, p: YaccProduction):
        """modifierName : term"""
        LOGGER.debug("p_modifierName: %s -> %r", p.slice[1], p[1])
        p[0] = CQLPrefixedName(p[1])

    def p_modifierValue(self, p: YaccProduction):
        """modifierValue : term"""
        LOGGER.debug("p_modifierValue: %s -> %r", p.slice[1], p[1])
        p[0] = p[1]

    def p_searchTerm(self, p: YaccProduction):
        """searchTerm : term"""
        LOGGER.debug("p_searchTerm: %s -> %r", p.slice[1], p[1])
        p[0] = p[1]

    def p_index(self, p: YaccProduction):
        """index : term"""
        LOGGER.debug("p_index: %s -> %r", p.slice[1], p[1])
        p[0] = CQLPrefixedName(p[1])

    def p_term(self, p: YaccProduction):
        # fmt: off
        """term : identifier
                | BOOL_AND
                | BOOL_OR
                | BOOL_NOT
                | BOOL_PROX
                | KEY_SORTBY"""
        # fmt: on
        LOGGER.debug("p_term: %s -> %r", p.slice[1], p[1])
        p[0] = p[1]

    def p_identifier(self, p: YaccProduction):
        # fmt: off
        """identifier : CHAR_STRING1
                      | CHAR_STRING2"""
        # fmt: on
        LOGGER.debug("p_identifier: %s", p.slice[1])
        p[0] = p[1]

    def p_error(self, p: YaccProduction):
        LOGGER.error("Parser stack: %s + %s", self.parser.symstack, p)

        if len(self.parser.symstack) >= 3:
            if (
                isinstance(self.parser.symstack[-2], YaccSymbol)
                and self.parser.symstack[-2].type in ("scopedClause",)
                and isinstance(self.parser.symstack[-1], LexToken)
                and self.parser.symstack[-1].type
                in ("BOOL_AND", "BOOL_OR", "BOOL_NOT", "BOOL_PROX")
            ):
                raise CQLParseError(
                    f"Missing right side for scopedClause at position {self.lexer.lexer.lexpos}."
                )

            if (
                isinstance(self.parser.symstack[-2], LexToken)
                and self.parser.symstack[-2].type == "LPAREN"
                and isinstance(self.parser.symstack[-1], YaccSymbol)
                and self.parser.symstack[-1].type
                in ("scopedClause", "cqlQuery", "term")
            ):
                raise CQLParseError(
                    f"Missing closing paranthesis at position {self.lexer.lexer.lexpos}."
                )

            # TODO: general check whether LPAREN on stack or found remaining RPAREN?

        if p is None:
            # missing symbols
            LOGGER.error(
                "Syntex error: EOF / no symbols left. Parser stack: %s",
                self.parser.symstack,
            )
        else:
            LOGGER.error("Syntex error: [lno:%d]: %s", p.lineno, p)

        raise CQLParseError("Parser error")


# ---------------------------------------------------------------------------


class CQLParser12(CQLParser11):
    start = "sortedQuery"

    # ---------------------------------------------------

    def p_sortedQuery(self, p: YaccProduction):
        # fmt: off
        """sortedQuery : prefixAssignmentGroup sortedQuery
                       | scopedClause KEY_SORTBY sortSpec
                       | scopedClause"""
        # fmt: on
        LOGGER.debug("p_sortedQuery: %s -> %s", p.slice[1:], p[1:])
        if len(p) == 4:
            p[1].add_sortSpecs(p[3])
            p[0] = p[1]
        elif len(p) == 3:
            LOGGER.debug("p_sortedQuery (assign prefix): %s <<- %s", p.slice[2], p[1])
            for prefix in p[1]:
                p[2].add_prefix(prefix)
            p[0] = p[2]
        else:
            p[0] = p[1]
        LOGGER.debug("stack@p_sortedQuery: %s", p.stack)
        if len(p.stack) == 1 and p.stack[0].type == "$end":
            p[0] = CQLQuery(p[0], version="1.2")

    def p_sortSpec(self, p: YaccProduction):
        # fmt: off
        """sortSpec : sortSpec singleSpec
                    | singleSpec"""
        # fmt: on
        LOGGER.debug("p_sortSpec: %s", p.slice[1:])
        if len(p) == 2:
            p[0] = list()
            p[0].append(p[1])
        else:
            if not isinstance(p[0], list):
                p[0] = list()
            p[0].extend(p[1])
            p[0].append(p[2])

    def p_singleSpec(self, p: YaccProduction):
        # fmt: off
        """singleSpec : index modifierList
                      | index"""
        # fmt: on
        LOGGER.debug("p_singleSpec: %s -> %r", p.slice[1:], p[1])
        if len(p) == 3:
            p[0] = CQLSortSpec(p[1], modifiers=p[2])
        else:
            p[0] = CQLSortSpec(p[1])

    def p_error(self, p: YaccProduction):
        if len(self.parser.symstack) >= 3:
            if (
                isinstance(self.parser.symstack[-2], YaccSymbol)
                and self.parser.symstack[-2].type == "scopedClause"
                and isinstance(self.parser.symstack[-1], LexToken)
                and self.parser.symstack[-1].type == "KEY_SORTBY"
            ):
                if p is None:
                    raise CQLParseError(
                        f"No sort key supplied at position {self.lexer.lexer.lexpos}. Unexpected end of input."
                    )
                else:
                    raise CQLParseError(
                        f"No sort key supplied at position {self.lexer.lexer.lexpos}. Found {p} symbol."
                    )

        super().p_error(p)


# ---------------------------------------------------------------------------
