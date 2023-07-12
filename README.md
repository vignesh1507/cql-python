# CQL (Contextual Query Language) Parser (for Python)

* [Grammar and Specification](http://www.loc.gov/standards/sru/cql/spec.html)

## Notice

Prefix parsing and resolution is still work-in-progress!
Test cases mostly check out but it definitely needs to be finished before
using in real world scenarios.

## Requires

* Python 3.8+ (only tested on 3.8.10)
* [`ply` _(github version)_](https://github.com/dabeaz/ply) - vendored in [`src/cql/_vendor/ply`](src/cql/_vendor/ply)
* [`pytest`](https://docs.pytest.org/) for testing

## Building

```bash
# see: https://setuptools.pypa.io/en/latest/build_meta.html
python3 -m pip install -q build
python3 -m build
```

## Install

```bash
# built package
python3 -m pip install dist/cql_parser-<version>-py2.py3-none-any.whl
# or
python3 -m pip install dist/cql-parser-<version>.tar.gz

# for local development
python3 -m pip install -e .[test]
```

## Usage

Really quick:
```python
import cql

print(cql.parse("dc.title any fish").toXCQLString(pretty=True))
```

A bit more involved:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

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

* Uses `pytest` (with coverage, clarity and randomly plugins).
* See test files in [`tests/`](tests/) folder. The **regression** test files are a copy from [`indexdata/cql-java`](https://github.com/indexdata/cql-java) and are not included in the built package. _The **XCQL** serialization differs slightly from the only [CQL Python 'library'](https://github.com/cheshire3/cheshire3/blob/develop/cheshire3/cqlParser.py) I could find._
* As for changing the lexer or parser, see [`ply` docs](http://www.dabeaz.com/ply/ply.html).

Run all tests with:
```bash
# install test dependencies
python3 -m install -e .[test]
# run
pytest
```

Run style checks:
```bash
python3 -m pip install -e .[style]
black --check .
flake8 . --show-source --statistics
isort --check --diff .

# building the package:
python3 -m pip install -e .[build]
python3 -m build
twine check --strict dist/*
```

Vendor dependencies:
```bash
python3 -m pip install -e .[vendor]
vendoring sync
# NOTE: some changes still not automated ...
git checkout -- src/cql/_vendor/ply/LICENSE
```

## See also

* http://zing.z3950.org/cql
* http://www.loc.gov/standards/sru/cql/index.html
* Other implementations: [Java](https://github.com/indexdata/cql-java), [JavaScript](https://github.com/Querela/cql-js), etc.
