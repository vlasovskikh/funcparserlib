Tokenizing Input
================

Parsing is usually split into two steps:

1. Tokenizing the input string into a sequence of tokens
2. Parsing the tokens into a parse tree


```
         ┌────────────┐               ┌─────────┐
   str   │            │  List[Token]  │         │   Expr
─────────► tokenize() ├───────────────► parse() ├─────────►
         │            │               │         │
         └────────────┘               └─────────┘
```

**Tokens** are larger pieces of the input text such as words, punctuation marks, spaces, etc. It's easier to parse a list of tokens than a string, since you can skip auxiliary tokens (spaces, newlines, commments) during tokenizing and focus on the main ones. Tokens usually track their position in the text, which is helpful in parsing error messages.


Tokenizing with `make_tokenizer()`
----------------------------------

One of the most common ways to define tokens and tokenizing rules is via regular expressions. `funcparserlib` comes with the module [`funcparserlib.lexer`](../api/lexer.md) for creating regexp-based tokenizers.

!!! Note

    Parsers defined with `funcparserlib` can work with _any_ tokens. You can plug your custom tokenizers and token types or even parse raw strings as lists of character tokens.

    In this guide we will use the _recommended_ way of writing tokenizers: `make_tokenizer()` from the `funcparserlib.lexer` module.

Let's identify token types in our numeric expressions language:

* Whitespace
    * Spaces, tabs, newlines
* Integer numbers
    * `0`, `256`, `-42`, ...
* Floating point numbers
    * `3.1415`, `27.1828e-01`, ...
* Operators
    * `(`, `)`, `*`, `+`, `/`, `-`, `**`

We will define our token specs and pass them to `make_tokenizer()` to generate our tokenizer. We will also drop whitespace tokens from the result, since we don't need them.

Some imports first:

```pycon
>>> from typing import List
>>> from funcparserlib.lexer import make_tokenizer, TokenSpec, Token

```

The tokenizer itself:

```pycon
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

!!! Warning

    Be careful with ordering your token specs and your regexps so that larger tokens come first before their smaller subparts. In our token specs:

    * _Float_ tokens should come before _int_ tokens
    * `**` should come before `*`

Let's try our tokenizer:

```pycon
>>> tokenize("42 + 1337")
[Token('int', '42'), Token('op', '+'), Token('int', '1337')]

```

The `str()` form of the token shows its position in the input text, also available via `t.start` and `t.end`:

```pycon
>>> [str(t) for t in tokenize("42 + 1337")]
["1,1-1,2: int '42'", "1,4-1,4: op '+'", "1,6-1,9: int '1337'"]

```


Next
----

We have tokenized an numeric expression string into a list of tokens.

In [the next chapter](parsing.md) you will learn how to parse these tokens by defining a grammar for our numeric expressions language.
