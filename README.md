# CQL (Contextual Query Language) Parser (for Python)

* [Grammar and Specification](http://www.loc.gov/standards/sru/cql/spec.html)

## Requires

* [`ply` _(github version)_](https://github.com/dabeaz/ply)
* [`pytest`](https://docs.pytest.org/) for testing

## Building

```bash
# see: https://setuptools.pypa.io/en/latest/build_meta.html
pip install -q build
python -m build
```

## Install

```bash
# built package
pip install dist/cql_parser-<version>-py2.py3-none-any.whl
# or
pip install dist/cql-parser-<version>.tar.gz

# for local development
pip install -e .[test]
```

## Usage

Really quick:
```python
import cql

print(cql.parse("dc.title any fish").toXCQLString(pretty=True))
```

A bit more involved:
```python
from cql.parser import CQLParser12

# use CQL version 1.2 parser
cqlparser = CQLParser12()
query = cqlparser.run("dc.title any fish")
# do something with the output
print(query.toCQL())
print(query.toXCQLString(pretty=True))
```

A for a deeper dive, take a look at [`src/cql/__init__.py`](src/cql/__init__.py) or the various test files in [`tests/`](tests/).

## Development

* Uses `pytest` (with coverage and clarity plugins).
* See test files in [`tests/`](tests/) folder. The **regression** test files are a copy from [`indexdata/cql-java`](https://github.com/indexdata/cql-java) and are not included in the built package. _The **XCQL** serialization differs slightly from the only [CQL Python 'library'](https://github.com/cheshire3/cheshire3/blob/develop/cheshire3/cqlParser.py) I could find._
* As for changing the lexer or parser, see [`ply` docs](http://www.dabeaz.com/ply/ply.html).

Run all tests with:
```bash
# install test dependencies
pip install -e .[test]
# run
pytest
```

Run style checks:
```bash
flake8
isort --diff src

# after building the package:
# twine check --strict dist/*
```