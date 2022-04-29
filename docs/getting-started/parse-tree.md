Preparing the Parse Tree
========================

So far we have defined the parser for our calculator expressions language:


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


>>> int_str = tok("int")
>>> float_str = tok("float")
>>> number = int_str | float_str
>>> expr = forward_decl()
>>> parenthesized = op("(") + expr + op(")")
>>> primary = number | parenthesized
>>> power = primary + many(op("**") + primary)
>>> expr.define(power)
>>> document = expr + finished

```

Here is how its parse results look so far:


```pycon
>>> document.parse(tokenize("2 ** (3 ** 4)"))
('2', [('**', ('(', ('3', [('**', '4')]), ')'))], None)

```


`p >> f`: Transforming Parse Results
------------------------------------

Let's start improving our parse results by converting numbers from `str` to `int` or `float`. We will use the [`Parser.__rshift__`](../api/parser.md#funcparserlib.parser.Parser.__rshift__) combinator for that. `p >> f` takes a parser `p` and a function `f` of a single argument and returns a new parser, that applies `f` to the parse result of `p`.

An integer parser that returns `int` values:

```pycon
>>> int_num: Parser[Token, int] = tok("int") >> int

```

!!! Note

    We specify the type hint for the parser only for clarity here. We wanted to highlight that `>>` here changes the output type of the parser from `str` to `int`. You may omit type hints for parsers and rely on type inference features of your text editor and type checker to get code completion and linting warnings:

    ```pycon
    >>> int_num = tok("int") >> int

    ```

    The only combinator which type is not inferrable is `forward_decl()`. You should specify its type explicitly to get your parser fully type checked.

Try it:


```pycon
>>> int_num.parse(tokenize("42"))
42

```

Let's redefine our `number` parser so that it returns either `int` or `float`:

```pycon
>>> from typing import Union


>>> float_num: Parser[Token, float] = tok("float") >> float
>>> number: Parser[Token, Union[int, float]] = int_num | float_num

```

Test it:

```pycon
>>> number.parse(tokenize("42"))
42

>>> number.parse(tokenize("3.14"))
3.14

```


`-p`: Skipping Parse Results
----------------------------

Let's recall our nested parenthesized numbers example:

```pycon
>>> p = forward_decl()
>>> p.define(number | (op("(") + p + op(")")))

```

Test it:

```pycon
>>> p.parse(tokenize("((1))"))
('(', ('(', 1, ')'), ')')

```

We have successfully parsed numbers in nested parentheses, but we don't want to see parentheses in the parsing results. Let's skip them using the [`Parser.__neg__`](../api/parser.md#funcparserlib.parser.Parser.__neg__) combinator. It allows you to skip any parts of a sequence of parsers concatenated via `p1 + p2 + ... + pN` by using a unary `-p` operator on the ones you want to skip:

```pycon
>>> p = forward_decl()
>>> p.define(number | (-op("(") + p + -op(")")))

```

The result is cleaner now:


```pycon
>>> p.parse(tokenize("1"))
1

>>> p.parse(tokenize("(1)"))
1

>>> p.parse(tokenize("((1))"))
1

```

Let's re-define our grammar using the [`Parser.__neg__`](../api/parser.md#funcparserlib.parser.Parser.__neg__) combinator to get rid of extra parentheses in the parse results, as well as of extra `None` returned by `finished`:

```pycon
>>> expr = forward_decl()
>>> parenthesized = -op("(") + expr + -op(")")
>>> primary = number | parenthesized
>>> power = primary + many(op("**") + primary)
>>> expr.define(power)
>>> document = expr + -finished

```

Test it:

```pycon
>>> document.parse(tokenize("2 ** (3 ** 4)"))
(2, [('**', (3, [('**', 4)]))])

```

User-Defined Classes for the Parse Tree
---------------------------------------

We have many types of binary operators in our grammar, but we've defined only the `**` power operator so far. Let's define them for `*`, `/`, `+`, `-` as well:

```pycon
>>> expr = forward_decl()
>>> parenthesized = -op("(") + expr + -op(")")
>>> primary = number | parenthesized
>>> power = primary + many(op("**") + primary)
>>> term = power + many((op("*") | op("/")) + power)
>>> sum = term + many((op("+") | op("-")) + term)
>>> expr.define(sum)
>>> document = expr + -finished

```

Here we've introduced a hierarchy of nested parsers: `expr -> sum -> term -> power -> primary -> parenthesized -> expr -> ...` to reflect the order of calculations set by our operator priorities: `+` < `*` < `**` < `()`.

Test it:


```pycon
>>> document.parse(tokenize("1 * (2 + 0) ** 3"))
(1, [], [('*', (2, [], [], [('+', (0, [], []))], [('**', 3)]))], [])

```

It's hard to understand the results without proper user-defined classes for our expression types. We actually have 3 expression types:

* Integer numbers
* Floating point numbers
* Binary expressions

For integers and floats we will use Python `int` and `float` classes. For binary expressions we'll introduce the `BinaryExpr` class:

```pycon
>>> from dataclasses import dataclass


>>> @dataclass
... class BinaryExpr:
...     op: str
...     left: "Expr"
...     right: "Expr"

```

Since we don't use a common base class for our expressions, we have to define `Expr` as a union of possible expression types:


```
>>> Expr = Union[BinaryExpr, int, float]

```

Now let's define a function to transform the parse results of our binary operators into `BinaryExpr` objects. Take a look at our parsers of various binary expressions. You can infer that each of them returns _(expression, list of (operator, expression))_. We will transform these nested tuples and lists into a tree of nested expressions by defining a function `to_expr(args)` and applying `>> to_expr` to our expression parsers:

```pycon
>>> from typing import Tuple


>>> def to_expr(args: Tuple[Expr, List[Tuple[str, Expr]]]) -> Expr:
...     first, rest = args
...     result = first
...     for op, expr in rest:
...         result = BinaryExpr(op, result, expr)
...     return result

```

Let's re-define our grammar using this transformation:


```pycon
>>> expr: Parser[Token, Expr] = forward_decl()
>>> parenthesized = -op("(") + expr + -op(")")
>>> primary = number | parenthesized
>>> power = primary + many(op("**") + primary) >> to_expr
>>> term = power + many((op("*") | op("/")) + power) >> to_expr
>>> sum = term + many((op("+") | op("-")) + term) >> to_expr
>>> expr.define(sum)
>>> document = expr + -finished

```

Test it:

```pycon
>>> document.parse(tokenize("3.1415926 * (2 + 7.18281828e-1) * 42"))
BinaryExpr(op='*', left=BinaryExpr(op='*', left=3.1415926, right=BinaryExpr(op='+', left=2, right=0.718281828)), right=42)

```

Let's pretty-print it using the [`pretty_tree(x, kids, show)`](../api/util.md#funcparserlib.util.pretty_tree) function:

```pycon
>>> from funcparserlib.util import pretty_tree


>>> def pretty_expr(expr: Expr) -> str:
... 
...     def kids(expr: Expr) -> List[Expr]:
...         if isinstance(expr, BinaryExpr):
...             return [expr.left, expr.right]
...         else:
...             return []
... 
...     def show(expr: Expr) -> str:
...         if isinstance(expr, BinaryExpr):
...             return f"BinaryExpr({expr.op!r})"
...         else:
...             return repr(expr)
... 
...     return pretty_tree(expr, kids, show)

```

Test it:

```pycon
>>> print(pretty_expr(document.parse(tokenize("3.1415926 * (2 + 7.18281828e-1) * 42"))))
BinaryExpr('*')
|-- BinaryExpr('*')
|   |-- 3.1415926
|   `-- BinaryExpr('+')
|       |-- 2
|       `-- 0.718281828
`-- 42

```



Finally, we have a proper parse tree that is easy to understand and work with!


Next
----


We've finished writing our numeric expressions parser.

If you want to learn more, let's discuss a few tips and tricks about parsing in [the next chapter](tips-and-tricks.md).
