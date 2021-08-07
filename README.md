funcparserlib
=============

Recursive descent parsing library for Python based on functional combinators.

[![PyPI](https://img.shields.io/pypi/v/funcparserlib)](https://pypi.org/project/funcparserlib/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/funcparserlib)](https://pypi.org/project/funcparserlib/)


Description
-----------

**Parser combinators** are just higher-order functions that take parsers as
their arguments and return them as result values. Parser combinators are:

  * First-class values
  * Extremely composable
  * Tend to make the code quite compact
  * Resemble the readable notation of xBNF grammars

Parsers made with `funcparserlib` are pure-Python LL(\*) parsers. It means that
it's **very easy to write them** without thinking about lookaheads and all
that hardcore parsing stuff. However, the recursive descent parsing is a rather
slow method compared to LL(k) or LR(k) algorithms.

So the primary domain for `funcparserlib` is **parsing little languages** or
**external DSLs** (domain specific languages).

The library itself is very small. Its source code is only 600 lines of code,
with lots of comments included. It features the longest parsed prefix error
reporting, as well as a tiny lexer generator for token position tracking.


Show Me the Code
----------------

This is an excerpt from a JSON parser
([RFC 4627](https://tools.ietf.org/html/rfc4627)) written using
`funcparserlib`. This full example as well as others can be found
[here](tests/json.py).

```python
def parse(seq):
    """Sequence(Token) -> object"""
    ...
    n = lambda s: tok("Name", s)
    def make_array(values):
        if values is None:
            return []
        else:
            return [values[0]] + values[1]
    ...
    null = n("null") >> const(None)
    true = n("true") >> const(True)
    false = n("false") >> const(False)
    number = tok("Number") >> make_number
    string = tok("String") >> make_string
    value = forward_decl()
    member = string + -op(":") + value >> tuple
    object = (
        -op("{") +
        maybe(member + many(-op(",") + member)) +
        -op("}")
        >> make_object)
    array = (
        -op("[") +
        maybe(value + many(-op(",") + value)) +
        -op("]")
        >> make_array)
    value.define(
          null
        | true
        | false
        | object
        | array
        | number
        | string)
    json_text = object | array
    json_file = json_text + -finished

    return json_file.parse(seq)
```


Installation
------------

You can install the `funcparserlib` library from
[PyPI](https://pypi.python.org/pypi/funcparserlib) via `pip`:

    $ pip install funcparserlib

There are no dependencies on other libraries.


Documentation
-------------

* [Nested Brackets Mini-HOWTO](doc/Brackets.md)
    * A short intro to `funcparserlib`
* [Tutorial](doc/Tutorial.md)
    * The comprehensive `funcparserlib` tutorial

See also comments inside the modules `funcparserlib.parser` and
`funcparserlib.lexer` or generate the API docs from the modules using `pydoc`.

There a couple of examples available in the tests/ directory:

* [GraphViz DOT parser](tests/dot.py)
* [JSON parser](tests/json.py)

See also [the changelog](docs/changes.md) and [FAQ](doc/FAQ.md).


Performance and Code Size
-------------------------

Despite being an LL(`*`) parser, `funcparserlib` has a reasonable performance.
For example, a JSON parser written using `funcparserlib` is 3 times faster
than a parser using the popular `pyparsing` library and only 5 times slower
than the specialized JSON library `simplejson` that uses _ad hoc_ parsing.
Here are some stats:

| **File Size** | **cjson** | **simplejson** | **funcparserlib** | **json-ply** | **pyparsing** |
|:--------------|:----------|:---------------|:------------------|:-------------|:--------------|
| 6 KB        | 0 ms    | 45 ms        | 228 ms          | n/a     | 802 ms      |
| 11 KB       | 0 ms    | 80 ms        | 395 ms          | 367 ms  | 1355 ms     |
| 100 KB      | 4 ms    | 148 ms       | 855 ms          | 1071 ms | 2611 ms     |
| 134 KB      | 11 ms   | 957 ms       | 4775 ms         | n/a     | 16534 ms    |
| 1009 KB     | 87 ms   | 6904 ms      | 36826 ms        | n/a     | 116510 ms   |
| **User Code**    | 0.9 KLOC | 0.8 KLOC | 0.1 KLOC | 0.5 KLOC | 0.1 KLOC |
| **Library Code** | 0 KLOC   | 0 KLOC   | 0.5 KLOC | 5.3 KLOC | 3.7 KLOC |

Both `funcparserlib` and `pyparsing` have the smallest user code size (that is
a common feature of parsing libraries compared to _ad hoc_ parsers). The
library code of `funcparserlib` is 7 times smaller (and much cleaner) than
`pyparsing`. The `json-ply` uses a LALR parser `ply` (similar to Yacc) and
performs like `funcparserlib`. `cjson` is a C library, hence the incredible
performance :)


Used By
-------

Some open-source projects that use `funcparserlib` as an explicit dependency:

* https://github.com/hylang/hy
    * 3.8K stars, version `>= 0.3.6`, Python 3.6+
* https://github.com/scrapinghub/splash
    * 3.3K stars, version `*`. Python 3 in Docker
* https://github.com/klen/graphite-beacon
    * 460 stars, version `==0.3.6`, Python 2 and 3
* https://github.com/blockdiag/blockdiag
    * 118 stars, version `*`, Python 3.5+
* https://github.com/pyta-uoft/pyta
    * 48 stars, version `*`, Python 3.8+


Usages in tests / secondary dependencies:

* https://github.com/buildbot/buildbot
    * 4.6K stars, version `== 0.3.6`
* https://github.com/quay/quay
    * 1.7K stars, version `==0.3.6`



Similar Projects
----------------

* [LEPL](https://code.google.com/p/lepl/). A recursive descent parsing
  library that uses two-way generators for backtracking. Its source code is
  rather large: 17 KLOC.
* [pyparsing](https://github.com/pyparsing/pyparsing/). A recursive descent
  parsing library. Probably the most popular Python parsing library.
  Nevertheless, its source code is quite dirty (though 4 KLOC only).
* [Monadic Parsing in Python](https://web.archive.org/web/20120507001413/http://sandersn.com/blog/?tag=/monads).
  A series of blog entries on monadic parsing.
* [Pysec (aka Parsec in Python)](http://www.valuedlessons.com/2008/02/pysec-monadic-combinatoric-parsing-in.html).
  A blog entry on monadic parsing, with nice syntax for Python.
