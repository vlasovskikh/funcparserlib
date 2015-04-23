funcparserlib
=============

A recurisve descent parsing library for Python based on functional combinators.

[![](https://drone.io/bitbucket.org/vlasovskikh/funcparserlib/status.png)](https://drone.io/bitbucket.org/vlasovskikh/funcparserlib/latest)


Description
-----------

_Parser combinators_ are just higher-order functions that take parsers as their arguments and return them as result values. Parser combinators are:

  * First-class values
  * Extremely composable
  * Tend to make the code quite compact
  * Resemble the readable notation of xBNF grammars

Parsers made with `funcparserlib` are pure-Python LL(`*`) parsers. It means that it's very easy to write them without thinking about look-aheads and all that hardcore parsing stuff. But the recursive descent parsing is a rather slow method compared to LL(k) or LR(k) algorithms.

So the primary domain for `funcparserlib` is **parsing little languages** or **external DSLs** (domain specific languages).

The library itself is very small. Its source code is only 0.5 KLOC, with lots of comments included. It features the longest parsed prefix error reporting, as well as a tiny lexer generator for token position tracking.


Installation
------------

You can install the `funcparserlib` library from [PyPI](https://pypi.python.org/pypi/funcparserlib) via `pip`:

    $ pip install funcparserlib

There are no dependencies on other libraries.


Documentation
-------------

The comprehensive [funcparserlib Tutorial][1] is available as `./doc/Tutorial.md`.

A short intro to `funcparserlib` can be found in the [Nested Brackets
Mini-HOWTO][2], see `./doc/Brackets.md`.

See also comments inside the modules `funcparserlib.parser` and
`funcparserlib.lexer` or generate the API docs from the modules using `pydoc`.

There a couple of examples available in `./examples` directory:

* GraphViz DOT parser
* JSON paser

See also [the changelog][3] and [FAQ][4].

  [1]: Tutorial
  [2]: Brackets
  [3]: Changes
  [4]: FAQ


Performance and Code Size
-------------------------

Despite being an LL(`*`) parser, `funcparserlib` has a reasonable performance. For example, a JSON parser written using `funcparserlib` is 3 times faster than a parser using the popular `pyparsing` library and only 5 times slower than the specialized JSON library `simplejson` that uses _ad hoc_ parsing. Here are some stats<sup>1</sup>:

| **File Size** | **cjson** | **simplejson** | **funcparserlib** | **json-ply** | **pyparsing** |
|:--------------|:----------|:---------------|:------------------|:-------------|:--------------|
| 6 KB        | 0 ms    | 45 ms        | 228 ms          | n/a     | 802 ms      |
| 11 KB       | 0 ms    | 80 ms        | 395 ms          | 367 ms  | 1355 ms     |
| 100 KB      | 4 ms    | 148 ms       | 855 ms          | 1071 ms | 2611 ms     |
| 134 KB      | 11 ms   | 957 ms       | 4775 ms         | n/a     | 16534 ms    |
| 1009 KB     | 87 ms   | 6904 ms      | 36826 ms        | n/a     | 116510 ms   |
| **User Code**    | 0.9 KLOC | 0.8 KLOC | 0.1 KLOC | 0.5 KLOC | 0.1 KLOC |
| **Library Code** | 0 KLOC   | 0 KLOC   | 0.5 KLOC | 5.3 KLOC | 3.7 KLOC |

`funcparserlib` and `pyparsing` both have the smallest user code size (that is a common feature of parsing libraries compared to _ad hoc_ parsers). The library code of `funcparserlib` is 7 times smaller (and much more cleaner) than `pyparsing`. The `json-ply` uses a LALR parser `ply` (similar to Yacc) and performs like `funcparserlib`. `cjson` is a C library, hence the incredible performance :)


Show Me the Code
----------------

This is an excerpt from a JSON parser ([RFC 4627](http://tools.ietf.org/html/rfc4627)). This full example as well as others can be found in `./examples` directory.

```python
def parse(seq):
    'Sequence(Token) -> object'
    ...
    n = lambda s: a(Token('Name', s)) >> tokval
    def make_array(n):
        if n is None:
            return []
        else:
            return [n[0]] + n[1]
    ...
    null = n('null') >> const(None)
    true = n('true') >> const(True)
    false = n('false') >> const(False)
    number = toktype('Number') >> make_number
    string = toktype('String') >> make_string
    value = forward_decl()
    member = string + op_(':') + value >> tuple
    object = (
        op_('{') +
        maybe(member + many(op_(',') + member)) +
        op_('}')
        >> make_object)
    array = (
        op_('[') +
        maybe(value + many(op_(',') + value)) +
        op_(']')
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
    json_file = json_text + skip(finished)

    return json_file.parse(seq)
```


Similar Projects
----------------

  * [LEPL](http://code.google.com/p/lepl/). A recursive descent parsing library that uses two-way generators for backtracking. Its source code is rather large: 17 KLOC
  * [pyparsing](http://pyparsing.wikispaces.com/). A recursive descent parsing library. Probably the most popular Python parsing library. Nevertheless its source code is quite dirty (though 4 KLOC only)
  * [Monadic Parsing in Python](http://sandersn.com/blog/index.php?title=monadic_parsing_in_python_part_3&more=1&c=1&tb=1&pb=1). A series of blog entries on monadic parsing
  * [Pysec (aka Parsec in Python)](http://www.valuedlessons.com/2008/02/pysec-monadic-combinatoric-parsing-in.html). A blog entry on monadic parsing, with nice syntax for Python


---


<sup>1</sup> Testing hardware: Pentium III, 1 GHz, 512 MB. JSON files were taken from a real project, in a normalized encoding, i. e. they contained no extra separators. The version 0.3.2 of the library was used.



<!-- vim:set ft=markdown tw=80: -->

