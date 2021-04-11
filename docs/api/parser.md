# `funcparserlib.parser` — Functional parsing combinators

::: funcparserlib.parser
    rendering:
        show_root_heading: false


::: funcparserlib.parser.Parser

::: funcparserlib.parser.Parser.parse
    rendering:
        heading_level: 3

::: funcparserlib.parser.Parser.define
    rendering:
        heading_level: 3

::: funcparserlib.parser.Parser.named
    rendering:
        heading_level: 3


Primitive Parsers
-----------------

::: funcparserlib.parser.a
    rendering:
        heading_level: 3

::: funcparserlib.parser.some
    rendering:
        heading_level: 3

::: funcparserlib.parser.forward_decl
    rendering:
        heading_level: 3

### `finished`

A parser that throws an exception if there are any unparsed tokens left in the sequence.

Type: `Parser[Any, None]`

**Examples:**

```pycon
>>> from funcparserlib.parser import a, finished
>>> expr = a("x") + finished
>>> expr.parse("x")
('x', None)

```

```pycon
>>> expr = a("x") + finished
>>> expr.parse("xy")
Traceback (most recent call last):
    ...
funcparserlib.parser.NoParseError: should have reached <EOF>: y

```


Parser Combinators
------------------

::: funcparserlib.parser.Parser.__add__
    rendering:
        heading_level: 3

::: funcparserlib.parser.Parser.__or__
    rendering:
        heading_level: 3

::: funcparserlib.parser.Parser.__rshift__
    rendering:
        heading_level: 3

::: funcparserlib.parser.maybe
    rendering:
        heading_level: 3

::: funcparserlib.parser.many
    rendering:
        heading_level: 3

::: funcparserlib.parser.oneplus
    rendering:
        heading_level: 3

::: funcparserlib.parser.skip
    rendering:
        heading_level: 3


Extra: Parser Monad
-------------------

As a functional programmer, you might be pleased to know, that parsers in funcparserlib
form _a monad_ with `Parser.bind()` as `>>=` and `pure()` as `return`.

We could have expressed other parsing combinators in terms of `bind()`, but would be
inefficient in Python:

```python
# noinspection PyUnresolvedReferences
class Parser:
    def __add__(self, other):
        return self.bind(lambda x: other.bind(lambda y: pure((x, y))))

    def __rshift__(self, other):
        return self.bind(lambda x: pure(x))
```

::: funcparserlib.parser.Parser.bind
    rendering:
        heading_level: 3

::: funcparserlib.parser.pure
    rendering:
        heading_level: 3
