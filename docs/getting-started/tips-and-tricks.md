Tips and Tricks
===============

Let's use the tokenizer we have defined previously for our examples in this chapter:

```pycon
>>> from typing import List
>>> from funcparserlib.lexer import make_tokenizer, TokenSpec, Token
>>> from funcparserlib.parser import tok, Parser, many, forward_decl, finished


>>> def tokenize(s: str) -> List[Token]:
...     specs = [
...         TokenSpec("whitespace", r"\s+"),
...         TokenSpec("float", r"[+\-]?\d+\.\d*([Ee][+\-]?\d+)*"),
...         TokenSpec("int", r"[+\-]?\d+"),
...         TokenSpec("op", r"(\*\*)|[+\-*/()]"),
...     ]
...     tokenizer = make_tokenizer(specs)
...     return [t for t in tokenizer(s) if t.type != "whitespace"]


>>> def op(name: str) -> Parser[Token, str]:
...     return tok("op", name)

```

## Name Alternative Parsers for Better Error Messages

Consider the following grammar:

```pycon
>>> number = (tok("int") >> int) | (tok("float") >> float)
>>> paren = -op("(") + number + -op(")")
>>> mul = number + op("*") + number
>>> expr = paren | mul

```

When a parser fails to parse its input, it usually reports the token it expects:

```pycon
>>> paren.parse(tokenize("(1"))   # doctest: +IGNORE_EXCEPTION_DETAIL
Traceback (most recent call last):
    ...
NoParseError: got unexpected end of input, expected: ')'

```

If there were several parsing alternatives, the parser will report an error after the longest successfully parsed sequence:

```pycon

>>> expr.parse(tokenize("1 + 2"))   # doctest: +IGNORE_EXCEPTION_DETAIL
Traceback (most recent call last):
    ...
NoParseError: 1,3-1,3: got unexpected token: '+', expected: '*'

```

If there were several parsing alternatives and all of them failed to parse the current token, then the parser will report its name as the expected input:

```pycon
>>> number.parse(tokenize("*"))   # doctest: +IGNORE_EXCEPTION_DETAIL
Traceback (most recent call last):
    ...
NoParseError: 1,1-1,1: got unexpected token: '*', expected: int or float

>>> expr.parse(tokenize("+"))   # doctest: +IGNORE_EXCEPTION_DETAIL
Traceback (most recent call last):
    ...
NoParseError: 1,1-1,1: got unexpected token: '+', expected: int or float or (('(', int or float), ')')

```

Parser names are auto-generated and may be quite long and hard to understand. For better error messages you may want to name your parsers explicitly via [`Parser.named(name)`](../api/parser.md#funcparserlib.parser.Parser.named). The naming style is up to you. For example:

```pycon
>>> number = ((tok("int") >> int) | (tok("float") >> float)).named("number")
>>> paren = -op("(") + number + -op(")")
>>> mul = number + op("*") + number
>>> expr = (paren | mul).named("number or '('")

```

Test it:


```pycon
>>> number.parse(tokenize("*"))   # doctest: +IGNORE_EXCEPTION_DETAIL
Traceback (most recent call last):
    ...
NoParseError: 1,1-1,1: got unexpected token: '*', expected: number

>>> expr.parse(tokenize("+"))   # doctest: +IGNORE_EXCEPTION_DETAIL
Traceback (most recent call last):
    ...
NoParseError: 1,1-1,1: got unexpected token: '+', expected: number or '('

```


## How to Handle Conflicting Alternatives

If one of the parsing alternatives is a subpart of another one, then you should put the longest alternative first. Otherwise parsing the shorter one will make another one unreachable:

```pycon
>>> p = (number + number) | (number + number + number)

>>> p.parse(tokenize("1 2 3"))
(1, 2)

```

Parse the longest alternative first:

```pycon
>>> p = (number + number + number) | (number + number)

>>> p.parse(tokenize("1 2 3"))
(1, 2, 3)

>>> p.parse(tokenize("1 2"))
(1, 2)

```


## Watch Out for Left Recursion

There are certain kinds grammar rules you cannot use with `funcparserlib`. These are the rules that contain recursion in their leftmost parts. These rules lead to infinite recursion during parsing, that results in a `RecursionError` exception.

For example, we want to define an expression `expr` either a multiplication operator `mul` or a `number`. We also want an expression to be a sequence of an expression `expr`, followed by an operator `"**"`, followed by another expression `expr`:


```pycon
>>> expr = forward_decl()
>>> mul = expr + op("*") + expr
>>> expr.define(mul | number)

```

This looks reasonable at the first glance, but it contains left recursion. In order to parse the first token for `expr`, we need to parse the first token for `mul`, for that we need to parse the first token for `expr`, and so on. This left recursion in your grammar results in a stack overflow exception:

```pycon
>>> expr.parse(tokenize("1 * 2"))   # doctest: +IGNORE_EXCEPTION_DETAIL
Traceback (most recent call last):
    ...
RecursionError: maximum recursion depth exceeded

```

You should think how to re-write your grammar to avoid left-recursive definitions. In our case of several multiplication operators we really want a number, followed by zero or more pairs of `*` and number:

```pycon
>>> expr = forward_decl()
>>> mul = number + many(op("**") + number)
>>> expr.define(mul)

```

Test it:

```pycon
>>> expr.parse(tokenize("1 ** 2"))
(1, [('**', 2)])


>>> expr.parse(tokenize("3"))
(3, [])

```

Remember that your parsers have to consume at least one token from the input before going into recursive defintions.
