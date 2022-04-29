Getting Started
===============


Intro
-----

In this guide, we will write **a parser for a numeric expression calculator** with a syntax similar to Python expressions. Writing a calculator is a common example in articles related to parsers and parsing techniques, so it is a good starting point in learning `funcparserlib`.

You will learn how to write a parser of numeric expressions using
`funcparserlib`. Here are some expression strings we want to be able to parse:

```
0
1 + 2 + 3
-1 + 2 ** 32
3.1415926 * (2 + 7.18281828e-1) * 42
```

We will parse these strings into trees of objects like this one:

```
BinaryExpr('*')
|-- BinaryExpr('*')
|   |-- 3.1415926
|   `-- BinaryExpr('+')
|       |-- 2
|       `-- 0.718281828
`-- 42
```


Diving In
---------

Here is the complete source code of the expression parser we are going to write.

You are **not** supposed to understand it now. Just look at its shape and try to get some feeling about its structure. By the end of this guide, **you will fully understand this code** and will be able to write parsers for your own needs.


```pycon
>>> from typing import List, Tuple, Union
>>> from dataclasses import dataclass
>>> from funcparserlib.lexer import make_tokenizer, TokenSpec, Token
>>> from funcparserlib.parser import tok, Parser, many, forward_decl, finished


>>> @dataclass
... class BinaryExpr:
...     op: str
...     left: "Expr"
...     right: "Expr"


>>> Expr = Union[BinaryExpr, int, float]


>>> def tokenize(s: str) -> List[Token]:
...     specs = [
...         TokenSpec("whitespace", r"\s+"),
...         TokenSpec("float", r"[+\-]?\d+\.\d*([Ee][+\-]?\d+)*"),
...         TokenSpec("int", r"[+\-]?\d+"),
...         TokenSpec("op", r"(\*\*)|[+\-*/()]"),
...     ]
...     tokenizer = make_tokenizer(specs)
...     return [t for t in tokenizer(s) if t.type != "whitespace"]


>>> def parse(tokens: List[Token]) -> Expr:
...     int_num = tok("int") >> int
...     float_num = tok("float") >> float
...     number = int_num | float_num
...
...     expr: Parser[Token, Expr] = forward_decl()
...     parenthesized = -op("(") + expr + -op(")")
...     primary = number | parenthesized
...     power = primary + many(op("**") + primary) >> to_expr
...     term = power + many((op("*") | op("/")) + power) >> to_expr
...     sum = term + many((op("+") | op("-")) + term) >> to_expr
...     expr.define(sum)
...
...     document = expr + -finished
...
...     return document.parse(tokens)


>>> def op(name: str) -> Parser[Token, str]:
...     return tok("op", name)


>>> def to_expr(args: Tuple[Expr, List[Tuple[str, Expr]]]) -> Expr:
...     first, rest = args
...     result = first
...     for op, expr in rest:
...         result = BinaryExpr(op, result, expr)
...     return result

```

!!! Note

    The code examples in this guide are actually executable. You can clone the [funcparserlib](https://github.com/vlasovskikh/funcparserlib) repository from GitHub and run the examples from the document via `doctest`:

    ```sh
    python3 -m doctest -v docs/getting-started/*.md

    ```

Test the expression parser:

```pycon
>>> parse(tokenize("0"))
0

>>> parse(tokenize("1 + 2 + 3"))
BinaryExpr(op='+', left=BinaryExpr(op='+', left=1, right=2), right=3)

>>> parse(tokenize("-1 + 2 ** 32"))
BinaryExpr(op='+', left=-1, right=BinaryExpr(op='**', left=2, right=32))

>>> parse(tokenize("3.1415926 * (2 + 7.18281828e-1) * 42"))
BinaryExpr(op='*', left=BinaryExpr(op='*', left=3.1415926, right=BinaryExpr(op='+', left=2, right=0.718281828)), right=42)

```


Next
----

Now let's start learning how to write a numeric expression parser using `funcparserlib`.

In [the next chapter](tokenizing.md) you will learn about the first step in parsing: tokenizing the input. It means splitting your input string into a sequence of tokens that are easier to parse.
