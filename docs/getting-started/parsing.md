Parsing Tokens
==============

So far we have defined the tokenizer for our calculator expressions language:

```pycon
>>> from typing import List
>>> from funcparserlib.lexer import make_tokenizer, TokenSpec, Token


>>> def tokenize(s: str) -> List[Token]:
...     specs = [
...         TokenSpec("whitespace", r"\s+"),
...         TokenSpec("float", r"[+\-]?\d+\.\d*([Ee][+\-]?\d+)*"),
...         TokenSpec("int", r"[+\-]?\d+"),
...         TokenSpec("op", r"(\*\*)|[+\-*/()]"),
...     ]
...     tokenizer = make_tokenizer(specs)
...     return [t for t in tokenizer(s) if t.type != "whitespace"]

```

It results a list of tokens which we want to parse according to our expressions grammar:

```pycon
>>> from pprint import pprint


>>> pprint(tokenize("3.1415926 * (2 + 7.18281828e-1) * 42"))
[Token('float', '3.1415926'),
 Token('op', '*'),
 Token('op', '('),
 Token('int', '2'),
 Token('op', '+'),
 Token('float', '7.18281828e-1'),
 Token('op', ')'),
 Token('op', '*'),
 Token('int', '42')]

```


Parser Combinators
------------------

A **parser** is an object that takes input tokens and transforms them into a parse result. For example, a **primitive parser** [`tok(type, value)`](../api/parser.md#funcparserlib.parser.tok) parses a single token of a certain type and, optionally, with a certain value.

Parsing a single token is not exciting at all. The interesting part comes when you start combining parsers via **parser combinators** to build bigger parsers of complex token sequences.

Parsers from [`funcparserlib.parser`](../api/parser.md) have a nice layered structure that allows you to express the grammar rules of the langauge you want to parse:

```
┌──────────┬──────────────────────┬───────────┐
│          │ Primitive Parsers    │           │
│          ├──────────────────────┘           │
│          │                                  │
│          │ tok(type, value)  forward_decl() │
│          │                                  │
│          │ a(token)  some(pred)  finished   │
│          │                                  │
│          ├──────────────────────┬───────────┤
│          │ Parser Combinators   │           │
│          ├──────────────────────┘           │
│          │                                  │
│  Parser  │ p1 + p2   p1 | p2   p >> f   -p  │
│  objects │                                  │
│          │ many(p)  oneplus(p)  maybe(p)    │
│          │                                  │
│          ├──────────────────────┬───────────┤
│          │ Means of Abstraction │           │
│          ├──────────────────────┘           │
│          │                                  │
│          │ Python assignments: =            │
│          │                                  │
│          │ Python functions: def            │
└──────────┴──────────────────────────────────┘
```

You get a new [`Parser`](../api/parser.md#funcparserlib.parser.Parser) object each time you apply a parser combinator to your parsers. Therefore, the set of all parsers it closed under the operations defined by parser combinators.

Parsers are regular Python objects of type [`Parser`](../api/parser.md#funcparserlib.parser.Parser). It means that you can write arbitrary Python code that builds parser objects: assign parsers to variables, pass parsers as call arguments, get them as the return values of calls, etc.

!!! Note

    The type [`Parser`](../api/parser.md#funcparserlib.parser.Parser) is actually parameterized as `Parser[T, V]` where:

    * `T` is the type of input tokens
    * `V` is the type of the parse result

    Your text editor or type checker will provide better code completion and error checking for your parsing code based on the types defined in `funcparserlib` and their type inference capabilities.


`tok()`: Parsing a Single Token
-------------------------------

Let's recall the expressions we would like to be able to parse:

```
0
1 + 2 + 3
-1 + 2 ** 32
3.1415926 * (2 + 7.18281828e-1) * 42
```

It looks like our grammar should have expressions that consist of numbers or nested expressions. Let's start with just numbers.


We'll use [`tok(type, value)`](../api/parser.md#funcparserlib.parser.tok) to create a primitive parser of a single integer token. Let's import it:

```pycon
>>> from funcparserlib.parser import tok

```

Here is our parser of a single integer token. The string `"int"` is the type of the integer token spec for our tokenizer:


```pycon
>>> int_str = tok("int")

```

Let's try it in action. In order to invoke a parser, we should pass a sequence of tokens to its [`Parser.parse(tokens)`](../api/parser.md#funcparserlib.parser.Parser.parse) method:

```pycon
>>> int_str.parse(tokenize("42"))
'42'

```

!!! Note

    Our parser returns integer numbers as strings at the moment. We'll cover transforming parse results and creating a proper parse tree in the next chapter.

If the first token in the input is _not_ of type `"int"`, our parser raises an exception:

```pycon
>>> int_str.parse(tokenize("+"))  # doctest: +IGNORE_EXCEPTION_DETAIL
Traceback (most recent call last):
    ...
NoParseError: 1,1-1,1: got unexpected token: '+', expected: int

```


`p1 | p2`: Parsing Alternatives
-------------------------------

We want to support floating point numbers as well. We already know how to do it:

```pycon
>>> float_str = tok("float")

```

Let's define our number expression as either an integer or a float number. We can parse alternatives using the [`Parser.__or__`](../api/parser.md#funcparserlib.parser.Parser.__or__) combinator:

```pycon
>>> number = int_str | float_str

```

Test it:

```pycon
>>> number.parse(tokenize("42"))
'42'

>>> number.parse(tokenize("3.14"))
'3.14'

>>> number.parse(tokenize("*"))  # doctest: +IGNORE_EXCEPTION_DETAIL
Traceback (most recent call last):
    ...
NoParseError: 1,1-1,1: got unexpected token: '*', expected: int or float

```


`p1 + p2`: Parsing a Sequence
-----------------------------

Since we can parse numbers now, let's proceeed with expressions. The first expression we will parse is the power operator:

```
2 ** 32
```

We need a new parser combinator to parse sequences of tokens. We can combine parsers sequentially using the [`Parser.__add__`](../api/parser.md#funcparserlib.parser.Parser.__add__) combinator.

Let's try it on sequences of numbers first:

```pycon
>>> p = number + number

```

Test it:

```pycon
>>> p.parse(tokenize("1 2"))
('1', '2')

```

The sequence combinator returns its results as a tuple of the parse results of its arguments. The size of the resulting tuple depends on the number of the parsers in the sequence. Let's try it for three numbers:

```pycon
>>> p = number + number + number

```

Test it:

```pycon
>>> p.parse(tokenize("1 2 3"))
('1', '2', '3')

```

Back to parsing the power operator of our calculator expressions language. We will need to parse several different operator tokens besides `"**"` in our grammar, so let's define a helper function:

```pycon
>>> from funcparserlib.parser import Parser


>>> def op(name: str) -> Parser[Token, str]:
...     return tok("op", name)

```

Let's define the parser of the power operator expressions using our new `op(name)` helper:

```pycon
>>> power = number + op("**") + number

```

Test it:

```pycon
>>> power.parse(tokenize("2 ** 32"))
('2', '**', '32')

```


`many()`: Parsing Repeated Parts
--------------------------------

We want to allow sequences of power operators. Let's parse the first number, followed by zero or more pairs of the power operator and a number. We'll use the [`many(p)`](../api/parser.md#funcparserlib.parser.many) combinator for that. Let's import it:

```pycon
>>> from funcparserlib.parser import many

```

Here is our parser of sequences of power operators:

```pycon
>>> power = number + many(op("**") + number)

```

Test it:

```pycon
>>> power.parse(tokenize("2 ** 3 ** 4"))
('2', [('**', '3'), ('**', '4')])

```

The `many(p)` combinator applies its argument parser `p` to the input sequence of tokens many times until it fails, returning a list of the results. If `p` fails to parse any tokens, `many(p)` still succeeds and returns an empty list:

```pycon
>>> power.parse(tokenize("1 + 2"))
('1', [])

```


`forward_decl()`: Parsing Recursive Parts
-----------------------------------------

We want to allow using parentheses to specify the order of calculations.

Ideally, we would like to write a recursive assignment like this one, but the Python syntax doesn't allow it:

```pycon
>>> expr = power | number | (op("(") + expr + op(")"))   # doctest: +IGNORE_EXCEPTION_DETAIL
Traceback (most recent call last):
    ...
NameError: name 'expr' is not defined

```

We will use the [`forward_decl()`](../api/parser.md#funcparserlib.parser.forward_decl) parser to solve the recursive assignment problem:

1. We create a forward declaration
2. We use the declaration in other parsers
3. We define the value of the declaration

Let's start with a simple example first. We'll create a parser numbers in properly nested parentheses:

```pycon
>>> from funcparserlib.parser import forward_decl
>>> p = forward_decl()
>>> p.define(number | (op("(") + p + op(")")))

```

Test it:

```pycon
>>> p.parse(tokenize("1"))
'1'

>>> p.parse(tokenize("(1)"))
('(', '1', ')')

>>> p.parse(tokenize("((1))"))
('(', ('(', '1', ')'), ')')

```

Back to our recursive `expr` problem. Let's re-write our grammar using `forward_decl()` for expressions:

```pycon
>>> expr = forward_decl()
>>> parenthesized = op("(") + expr + op(")")
>>> primary = number | parenthesized
>>> power = primary + many(op("**") + primary)
>>> expr.define(power)

```

Test it:

```pycon
>>> expr.parse(tokenize("2 ** 3 ** 4"))
('2', [('**', '3'), ('**', '4')])

>>> expr.parse(tokenize("2 ** (3 ** 4)"))
('2', [('**', ('(', ('3', [('**', '4')]), ')'))])

```


`finished`: Expecting No More Input
-----------------------------------

Surprisingly, our `expr` parser tolerates incomplete expressions by ignoring the incomplete parts:

```pycon
>>> expr.parse(tokenize("2 ** (3 ** 4"))
('2', [])

```

The problem is that its `many(p)` part parses the input while `p` succeeds, and it doesn't look any further than that. We can make a parser expect the end of the input via the [`finished`](../api/parser.md#finished) parser. Let's define a parser for the whole input document:

```pycon
>>> from funcparserlib.parser import finished
>>> document = expr + finished

```

!!! Note

    Usually you finish the topmost parser of your grammar with `... + finished` to indicate that you expect no further input.

Let's try it for our grammar:

```pycon
>>> document.parse(tokenize("2 ** (3 ** 4"))   # doctest: +IGNORE_EXCEPTION_DETAIL
Traceback (most recent call last):
    ...
NoParseError: got unexpected end of input, expected: ')'

>>> document.parse(tokenize("2 ** (3 ** 4)"))
('2', [('**', ('(', ('3', [('**', '4')]), ')'))], None)

```

Next
----

We have created a parser for power operator expressions. Its parse results are correct, but they look hard to undersand and work with:

* Our integer and floating point numbers are strings, not `int` or `float` objects
* The results contain `'('` and `')'` strings even though we need parentheses only temporarily to set the operator priorities
* The results contain `None`, which is the parse result of [`finished`](../api/parser.md#finished), even though we don't need it
* The results are lists of tuples of strings, not user-defined classes that reflect the grammar of our calculator expressions language

In [the next chapter](parse-tree.md) you will learn how to transform parse results and prepare a proper, cleaned up parse tree.
