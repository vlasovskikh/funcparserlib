# Copyright © 2009/2023 Andrey Vlasovskikh
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to the following
# conditions:
#
# The above copyright notice and this permission notice shall be included in all copies
# or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NON-INFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
# CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""Functional parsing combinators.

Parsing combinators define an internal domain-specific language (DSL) for describing
the parsing rules of a grammar. The DSL allows you to start with a few primitive
parsers, then combine your parsers to get more complex ones, and finally cover
the whole grammar you want to parse.

The structure of the language:

* Class `Parser`
    * All the primitives and combinators of the language return `Parser` objects
    * It defines the main `Parser.parse(tokens)` method
* Primitive parsers
    * `tok(type, value)`, `a(value)`, `some(pred)`, `forward_decl()`, `finished`
* Parser combinators
    * `p1 + p2`, `p1 | p2`, `p >> f`, `-p`, `maybe(p)`, `many(p)`, `oneplus(p)`,
      `skip(p)`
* Abstraction
    * Use regular Python variables `p = ...  # Expression of type Parser` to define new
      rules (non-terminals) of your grammar

Every time you apply one of the combinators, you get a new `Parser` object. In other
words, the set of `Parser` objects is closed under the means of combination.

!!! Note

    We took the parsing combinators language from the book [Introduction to Functional
    Programming][1] and translated it from ML into Python.

  [1]: https://www.cl.cam.ac.uk/teaching/Lectures/funprog-jrh-1996/
"""

__all__ = [
    "some",
    "a",
    "tok",
    "many",
    "pure",
    "finished",
    "maybe",
    "skip",
    "oneplus",
    "forward_decl",
    "NoParseError",
    "Parser",
]

import logging
import warnings
from typing import (
    Any,
    Callable,
    Generic,
    List,
    Optional,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    cast,
    overload,
)

from funcparserlib.lexer import Token

log = logging.getLogger("funcparserlib")

debug = False

_A = TypeVar("_A")
_B = TypeVar("_B")
_C = TypeVar("_C")


class Parser(Generic[_A, _B]):
    """A parser object that can parse a sequence of tokens or can be combined with
    other parsers using `+`, `|`, `>>`, `many()`, and other parsing combinators.

    Type: `Parser[A, B]`

    The generic variables in the type are: `A` — the type of the tokens in the
    sequence to parse,`B` — the type of the parsed value.

    In order to define a parser for your grammar:

    1. You start with primitive parsers by calling `a(value)`, `some(pred)`,
       `forward_decl()`, `finished`
    2. You use parsing combinators `p1 + p2`, `p1 | p2`, `p >> f`, `many(p)`, and
       others to combine parsers into a more complex parser
    3. You can assign complex parsers to variables to define names that correspond to
       the rules of your grammar

    !!! Note

        The constructor `Parser.__init__()` is considered **internal** and may be
        changed in future versions. Use primitive parsers and parsing combinators to
        construct new parsers.
    """

    def __init__(
        self,
        p: Union[
            "Parser[_A, _B]",
            Callable[[Sequence[_A], "State"], Tuple[_B, "State"]],
        ],
    ) -> None:
        """Wrap the parser function `p` into a `Parser` object."""
        self.name = ""
        self.define(p)

    def named(self, name: str) -> "Parser[_A, _B]":
        # noinspection GrazieInspection
        """Specify the name of the parser for easier debugging.

        Type: `(str) -> Parser[A, B]`

        This name is used in the debug-level parsing log. You can also get it via the
        `Parser.name` attribute.

        Examples:

        ```pycon
        >>> expr = (a("x") + a("y")).named("expr")
        >>> expr.name
        'expr'

        ```

        ```pycon
        >>> expr = a("x") + a("y")
        >>> expr.name
        "('x', 'y')"

        ```

        !!! Note

            You can enable the parsing log this way:

            ```python
            import logging
            logging.basicConfig(level=logging.DEBUG)
            import funcparserlib.parser
            funcparserlib.parser.debug = True
            ```

            The way to enable the parsing log may be changed in future versions.
        """
        self.name = name
        return self

    def define(
        self,
        p: Union[
            "Parser[_A, _B]",
            Callable[[Sequence[_A], "State"], Tuple[_B, "State"]],
        ],
    ) -> None:
        """Define the parser created earlier as a forward declaration.

        Type: `(Parser[A, B]) -> None`

        Use `p = forward_decl()` in combination with `p.define(...)` to define
        recursive parsers.

        See the examples in the docs for `forward_decl()`.
        """
        f = getattr(p, "run", p)
        if debug:
            setattr(self, "_run", f)
        else:
            setattr(self, "run", f)
        name = getattr(p, "name", p.__doc__)
        if name is not None:
            self.named(name)

    def run(self, tokens: Sequence[_A], s: "State") -> Tuple[_B, "State"]:
        """Run the parser against the tokens with the specified parsing state.

        Type: `(Sequence[A], State) -> Tuple[B, State]`

        The parsing state includes the current position in the sequence being parsed,
        and the position of the rightmost token that has been consumed while parsing for
        better error messages.

        If the parser fails to parse the tokens, it raises `NoParseError`.

        !!! Warning

            This is method is **internal** and may be changed in future versions. Use
            `Parser.parse(tokens)` instead and let the parser object take care of
            updating the parsing state.
        """
        if debug:
            log.debug("trying %s" % self.name)
        return self._run(tokens, s)

    def _run(self, tokens: Sequence[_A], s: "State") -> Tuple[_B, "State"]:
        raise NotImplementedError("you must define() a parser")

    def parse(self, tokens: Sequence[_A]) -> _B:
        """Parse the sequence of tokens and return the parsed value.

        Type: `(Sequence[A]) -> B`

        It takes a sequence of tokens of arbitrary type `A` and returns the parsed value
        of arbitrary type `B`.

        If the parser fails to parse the tokens, it raises `NoParseError`.

        !!! Note

            Although `Parser.parse()` can parse sequences of any objects (including
            `str` which is a sequence of `str` chars), **the recommended way** is
            parsing sequences of `Token` objects.

            You **should** use a regexp-based tokenizer `make_tokenizer()` defined in
            `funcparserlib.lexer` to convert your text into a sequence of `Token`
            objects before parsing it. You will get more readable parsing error messages
            (as `Token` objects contain their position in the source file) and good
            separation of the lexical and syntactic levels of the grammar.
        """
        try:
            (tree, _) = self.run(tokens, State(0, 0, None))
            return tree
        except NoParseError as e:
            max = e.state.max
            if len(tokens) > max:
                t = tokens[max]
                if isinstance(t, Token):
                    if t.start is None or t.end is None:
                        loc = ""
                    else:
                        s_line, s_pos = t.start
                        e_line, e_pos = t.end
                        loc = "%d,%d-%d,%d: " % (s_line, s_pos, e_line, e_pos)
                    msg = "%s%s: %r" % (loc, e.msg, t.value)
                elif isinstance(t, str):
                    msg = "%s: %r" % (e.msg, t)
                else:
                    msg = "%s: %s" % (e.msg, t)
            else:
                msg = "got unexpected end of input"
            e_parser = e.state.parser
            if isinstance(e_parser, Parser):
                msg = "%s, expected: %s" % (msg, e_parser.name)
            e.msg = msg
            raise

    @overload
    def __add__(  # type: ignore[misc]
        self, other: "_IgnoredParser[_A]"
    ) -> "Parser[_A, _B]":
        pass

    @overload
    def __add__(self, other: "Parser[_A, _C]") -> "_TupleParser[_A, Tuple[_B, _C]]":
        pass

    def __add__(
        self,
        other: Union["_IgnoredParser[_A]", "Parser[_A, _C]"],
    ) -> Union["Parser[_A, _B]", "_TupleParser[_A, Tuple[_B, _C]]"]:
        """Sequential combination of parsers. It runs this parser, then the other
        parser.

        The return value of the resulting parser is a tuple of each parsed value in
        the sum of parsers. We merge all parsing results of `p1 + p2 + ... + pN` into a
        single tuple. It means that the parsing result may be a 2-tuple, a 3-tuple,
        a 4-tuple, etc. of parsed values. You avoid this by transforming the parsed
        pair into a new value using the `>>` combinator.

        You can also skip some parsing results in the resulting parsers by using `-p`
        or `skip(p)` for some parsers in your sum of parsers. It means that the parsing
        result might be a single value, not a tuple of parsed values. See the docs
        for `Parser.__neg__()` for more examples.

        Overloaded types (lots of them to provide stricter checking for the quite
        dynamic return type of this method):

        * `(self: Parser[A, B], _IgnoredParser[A]) -> Parser[A, B]`
        * `(self: Parser[A, B], Parser[A, C]) -> _TupleParser[A, Tuple[B, C]]`
        * `(self: _TupleParser[A, B], _IgnoredParser[A]) -> _TupleParser[A, B]`
        * `(self: _TupleParser[A, B], Parser[A, Any]) -> Parser[A, Any]`
        * `(self: _IgnoredParser[A], _IgnoredParser[A]) -> _IgnoredParser[A]`
        * `(self: _IgnoredParser[A], Parser[A, C]) -> Parser[A, C]`

        Examples:

        ```pycon
        >>> expr = a("x") + a("y")
        >>> expr.parse("xy")
        ('x', 'y')

        ```

        ```pycon
        >>> expr = a("x") + a("y") + a("z")
        >>> expr.parse("xyz")
        ('x', 'y', 'z')

        ```

        ```pycon
        >>> expr = a("x") + a("y")
        >>> expr.parse("xz")
        Traceback (most recent call last):
            ...
        parser.NoParseError: got unexpected token: 'z', expected: 'y'

        ```
        """

        def magic(v1: Any, v2: Any) -> _Tuple:
            if isinstance(v1, _Tuple):
                return _Tuple(v1 + (v2,))
            else:
                return _Tuple((v1, v2))

        @_TupleParser
        def _add(tokens: Sequence[_A], s: State) -> Tuple[Tuple[_B, _C], State]:
            (v1, s2) = self.run(tokens, s)
            (v2, s3) = other.run(tokens, s2)
            return cast(Tuple[_B, _C], magic(v1, v2)), s3

        @Parser
        def ignored_right(tokens: Sequence[_A], s: State) -> Tuple[_B, State]:
            v, s2 = self.run(tokens, s)
            _, s3 = other.run(tokens, s2)
            return v, s3

        name = "(%s, %s)" % (self.name, other.name)
        if isinstance(other, _IgnoredParser):
            return ignored_right.named(name)
        else:
            _add.name = name
            return _add

    def __or__(self, other: "Parser[_A, _C]") -> "Parser[_A, Union[_B, _C]]":
        """Choice combination of parsers.

        It runs this parser and returns its result. If the parser fails, it runs the
        other parser.

        Examples:

        ```pycon
        >>> expr = a("x") | a("y")
        >>> expr.parse("x")
        'x'
        >>> expr.parse("y")
        'y'
        >>> expr.parse("z")
        Traceback (most recent call last):
            ...
        parser.NoParseError: got unexpected token: 'z', expected: 'x' or 'y'

        ```
        """

        @Parser
        def _or(tokens: Sequence[_A], s: State) -> Tuple[Union[_B, _C], State]:
            try:
                return self.run(tokens, s)
            except NoParseError as e:
                state = e.state
            try:
                return other.run(tokens, State(s.pos, state.max, state.parser))
            except NoParseError as e:
                if s.pos == e.state.max:
                    e.state = State(e.state.pos, e.state.max, _or)
                raise

        _or.name = "%s or %s" % (self.name, other.name)
        return _or

    def __rshift__(self, f: Callable[[_B], _C]) -> "Parser[_A, _C]":
        """Transform the parsing result by applying the specified function.

        Type: `(Callable[[B], C]) -> Parser[A, C]`

        You can use it for transforming the parsed value into another value before
        including it into the parse tree (the AST).

        Examples:

        ```pycon
        >>> def make_canonical_name(s):
        ...     return s.lower()
        >>> expr = (a("D") | a("d")) >> make_canonical_name
        >>> expr.parse("D")
        'd'
        >>> expr.parse("d")
        'd'

        ```
        """

        @Parser
        def _shift(tokens: Sequence[_A], s: State) -> Tuple[_C, State]:
            (v, s2) = self.run(tokens, s)
            return f(v), s2

        return _shift.named(self.name)

    def bind(self, f: Callable[[_B], "Parser[_A, _C]"]) -> "Parser[_A, _C]":
        """Bind the parser to a monadic function that returns a new parser.

        Type: `(Callable[[B], Parser[A, C]]) -> Parser[A, C]`

        Also known as `>>=` in Haskell.

        !!! Note

            You can parse any context-free grammar without resorting to `bind`. Due
            to its poor performance please use it only when you really need it.
        """

        @Parser
        def _bind(tokens: Sequence[_A], s: State) -> Tuple[_C, State]:
            (v, s2) = self.run(tokens, s)
            return f(v).run(tokens, s2)

        _bind.name = "(%s >>=)" % (self.name,)
        return _bind

    def __neg__(self) -> "_IgnoredParser[_A]":
        """Return a parser that parses the same tokens, but its parsing result is
        ignored by the sequential `+` combinator.

        Type: `(Parser[A, B]) -> _IgnoredParser[A]`

        You can use it for throwing away elements of concrete syntax (e.g. `","`,
        `";"`).

        Examples:

        ```pycon
        >>> expr = -a("x") + a("y")
        >>> expr.parse("xy")
        'y'

        ```

        ```pycon
        >>> expr = a("x") + -a("y")
        >>> expr.parse("xy")
        'x'

        ```

        ```pycon
        >>> expr = a("x") + -a("y") + a("z")
        >>> expr.parse("xyz")
        ('x', 'z')

        ```

        ```pycon
        >>> expr = -a("x") + a("y") + -a("z")
        >>> expr.parse("xyz")
        'y'

        ```

        ```pycon
        >>> expr = -a("x") + a("y")
        >>> expr.parse("yz")
        Traceback (most recent call last):
            ...
        parser.NoParseError: got unexpected token: 'y', expected: 'x'

        ```

        ```pycon
        >>> expr = a("x") + -a("y")
        >>> expr.parse("xz")
        Traceback (most recent call last):
            ...
        parser.NoParseError: got unexpected token: 'z', expected: 'y'

        ```

        !!! Note

            You **should not** pass the resulting parser to any combinators other than
            `+`. You **should** have at least one non-skipped value in your
            `p1 + p2 + ... + pN`. The parsed value of `-p` is an **internal** `_Ignored`
            object, not intended for actual use.
        """
        return _IgnoredParser(self)


class State:
    """Parsing state that is maintained basically for error reporting.

    It consists of the current position `pos` in the sequence being parsed, and the
    position `max` of the rightmost token that has been consumed while parsing.
    """

    def __init__(
        self,
        pos: int,
        max: int,
        parser: Union[
            Parser,
            Callable[[Any, "State"], Tuple[Any, "State"]],
            None,
        ] = None,
    ) -> None:
        self.pos = pos
        self.max = max
        self.parser = parser

    def __str__(self) -> str:
        return str((self.pos, self.max))

    def __repr__(self) -> str:
        return "State(%r, %r)" % (self.pos, self.max)


class NoParseError(Exception):
    def __init__(self, msg: str, state: State) -> None:
        self.msg = msg
        self.state = state

    def __str__(self) -> str:
        return self.msg


class _Tuple(tuple):
    pass


class _TupleParser(Parser[_A, _B], Generic[_A, _B]):
    @overload  # type: ignore[override]
    def __add__(self, other: "_IgnoredParser[_A]") -> "_TupleParser[_A, _B]":
        pass

    @overload
    def __add__(self, other: Parser[_A, Any]) -> Parser[_A, Any]:
        pass

    def __add__(
        self, other: Union["_IgnoredParser[_A]", Parser[_A, Any]]
    ) -> Union["_TupleParser[_A, _B]", Parser[_A, Any]]:
        return super().__add__(other)


class _Ignored:
    def __init__(self, value: Any) -> None:
        self.value = value

    def __repr__(self) -> str:
        return "_Ignored(%s)" % repr(self.value)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _Ignored) and self.value == other.value


@Parser
def finished(tokens: Sequence[Any], s: State) -> Tuple[None, State]:
    """A parser that throws an exception if there are any unparsed tokens left in the
    sequence."""
    if s.pos >= len(tokens):
        return None, s
    else:
        s2 = State(s.pos, s.max, finished if s.pos == s.max else s.parser)
        raise NoParseError("got unexpected token", s2)


finished.name = "end of input"


def many(p: Parser[_A, _B]) -> Parser[_A, List[_B]]:
    """Return a parser that applies the parser `p` as many times as it succeeds at
    parsing the tokens.

    Return a parser that infinitely applies the parser `p` to the input sequence
    of tokens as long as it successfully parses them. The parsed value is a list of
    the sequentially parsed values.

    Examples:

    ```pycon
    >>> expr = many(a("x"))
    >>> expr.parse("x")
    ['x']
    >>> expr.parse("xx")
    ['x', 'x']
    >>> expr.parse("xxxy")  # noqa
    ['x', 'x', 'x']
    >>> expr.parse("y")
    []

    ```
    """

    @Parser
    def _many(tokens: Sequence[_A], s: State) -> Tuple[List[_B], State]:
        res = []
        try:
            while True:
                (v, s) = p.run(tokens, s)
                res.append(v)
        except NoParseError as e:
            s2 = State(s.pos, e.state.max, e.state.parser)
            if debug:
                log.debug(
                    "*matched* %d instances of %s, new state = %s"
                    % (len(res), _many.name, s2)
                )
            return res, s2

    _many.name = "{ %s }" % p.name
    return _many


def some(pred: Callable[[_A], bool]) -> Parser[_A, _A]:
    """Return a parser that parses a token if it satisfies the predicate `pred`.

    Type: `(Callable[[A], bool]) -> Parser[A, A]`

    Examples:

    ```pycon
    >>> expr = some(lambda s: s.isalpha()).named('alpha')
    >>> expr.parse("x")
    'x'
    >>> expr.parse("y")
    'y'
    >>> expr.parse("1")
    Traceback (most recent call last):
        ...
    parser.NoParseError: got unexpected token: '1', expected: alpha

    ```

    !!! Warning

        The `some()` combinator is quite slow and may be changed or removed in future
        versions. If you need a parser for a token by its type (e.g. any identifier)
        and maybe its value, use `tok(type[, value])` instead. You should use
        `make_tokenizer()` from `funcparserlib.lexer` to tokenize your text first.
    """

    @Parser
    def _some(tokens: Sequence[_A], s: State) -> Tuple[_A, State]:
        if s.pos >= len(tokens):
            s2 = State(s.pos, s.max, _some if s.pos == s.max else s.parser)
            raise NoParseError("got unexpected end of input", s2)
        else:
            t = tokens[s.pos]
            if pred(t):
                pos = s.pos + 1
                s2 = State(pos, max(pos, s.max), s.parser)
                if debug:
                    log.debug("*matched* %r, new state = %s" % (t, s2))
                return t, s2
            else:
                s2 = State(s.pos, s.max, _some if s.pos == s.max else s.parser)
                if debug and isinstance(s2.parser, Parser):
                    log.debug(
                        "failed %r, state = %s, expected = %s" % (t, s2, s2.parser.name)
                    )
                raise NoParseError("got unexpected token", s2)

    _some.name = "some(...)"
    return _some


def a(value: _A) -> Parser[_A, _A]:
    """Return a parser that parses a token if it's equal to `value`.

    Type: `(A) -> Parser[A, A]`

    Examples:

    ```pycon
    >>> expr = a("x")
    >>> expr.parse("x")
    'x'
    >>> expr.parse("y")
    Traceback (most recent call last):
        ...
    parser.NoParseError: got unexpected token: 'y', expected: 'x'

    ```

    !!! Note

        Although `Parser.parse()` can parse sequences of any objects (including
        `str` which is a sequence of `str` chars), **the recommended way** is
        parsing sequences of `Token` objects.

        You **should** use a regexp-based tokenizer `make_tokenizer()` defined in
        `funcparserlib.lexer` to convert your text into a sequence of `Token` objects
        before parsing it. You will get more readable parsing error messages (as `Token`
        objects contain their position in the source file) and good separation of the
        lexical and syntactic levels of the grammar.
    """
    name = getattr(value, "name", value)

    def eq_value(t: _A) -> bool:
        return t == value

    return some(eq_value).named(repr(name))


def tok(type: str, value: Optional[str] = None) -> Parser[Token, str]:
    """Return a parser that parses a `Token` and returns the string value of the token.

    Type: `(str, Optional[str]) -> Parser[Token, str]`

    You can match any token of the specified `type` or you can match a specific token by
    its `type` and `value`.

    Examples:

    ```pycon
    >>> expr = tok("expr")
    >>> expr.parse([Token("expr", "foo")])
    'foo'
    >>> expr.parse([Token("expr", "bar")])
    'bar'
    >>> expr.parse([Token("op", "=")])
    Traceback (most recent call last):
        ...
    parser.NoParseError: got unexpected token: '=', expected: expr

    ```

    ```pycon
    >>> expr = tok("op", "=")
    >>> expr.parse([Token("op", "=")])
    '='
    >>> expr.parse([Token("op", "+")])
    Traceback (most recent call last):
        ...
    parser.NoParseError: got unexpected token: '+', expected: '='

    ```

    !!! Note

        In order to convert your text to parse into a sequence of `Token` objects,
        use a regexp-based tokenizer `make_tokenizer()` defined in
        `funcparserlib.lexer`. You will get more readable parsing error messages (as
        `Token` objects contain their position in the source file) and good separation
        of the lexical and syntactic levels of the grammar.
    """

    def eq_type(t: Token) -> bool:
        return t.type == type

    if value is not None:
        p = a(Token(type, value))
    else:
        p = some(eq_type).named(type)
    return (p >> (lambda t: t.value)).named(p.name)


def pure(x: _A) -> Parser[Any, _A]:
    """Wrap any object into a parser.

    Type: `(A) -> Parser[A, A]`

    A pure parser doesn't touch the tokens sequence, it just returns its pure `x`
    value.

    Also known as `return` in Haskell.
    """

    @Parser
    def _pure(_: Sequence[Any], s: State) -> Tuple[_A, State]:
        return x, s

    _pure.name = "(pure %r)" % (x,)
    return _pure


def maybe(p: Parser[_A, _B]) -> Parser[_A, Optional[_B]]:
    """Return a parser that returns `None` if the parser `p` fails.

    Examples:

    ```pycon
    >>> expr = maybe(a("x"))
    >>> expr.parse("x")
    'x'
    >>> expr.parse("y") is None
    True

    ```
    """
    return (p | pure(None)).named("[ %s ]" % (p.name,))


def skip(p: Parser[_A, Any]) -> "_IgnoredParser[_A]":
    """An alias for `-p`.

    See also the docs for `Parser.__neg__()`.
    """
    return -p


class _IgnoredParser(Parser[_A, Any]):
    def __init__(
        self,
        p: Union[
            Parser[_A, Any],
            Callable[[Sequence[_A], "State"], Tuple[Any, "State"]],
        ],
    ) -> None:
        super(_IgnoredParser, self).__init__(p)
        run = self._run if debug else self.run

        def ignored(tokens: Sequence[_A], s: State) -> Tuple[Any, State]:
            v, s2 = run(tokens, s)
            return v if isinstance(v, _Ignored) else _Ignored(v), s2

        self.define(ignored)
        name = getattr(p, "name", p.__doc__)
        if name is not None:
            self.name = name

    @overload  # type: ignore[override]
    def __add__(self, other: "_IgnoredParser[_A]") -> "_IgnoredParser[_A]":
        pass

    @overload
    def __add__(self, other: Parser[_A, _C]) -> Parser[_A, _C]:
        pass

    def __add__(
        self, other: Union["_IgnoredParser[_A]", Parser[_A, _C]]
    ) -> Union["_IgnoredParser[_A]", Parser[_A, _C]]:
        if isinstance(other, _IgnoredParser):

            @_IgnoredParser
            def ip(tokens: Sequence[_A], s: State) -> Tuple[Any, State]:
                _, s2 = self.run(tokens, s)
                v, s3 = other.run(tokens, s2)
                return v, s3

            ip.name = "(%s, %s)" % (self.name, other.name)
            return ip
        else:

            @Parser
            def p(tokens: Sequence[_A], s: State) -> Tuple[_C, State]:
                _, s2 = self.run(tokens, s)
                v, s3 = other.run(tokens, s2)
                return v, s3

            p.name = "(%s, %s)" % (self.name, other.name)
            return p


def oneplus(p: Parser[_A, _B]) -> Parser[_A, List[_B]]:
    """Return a parser that applies the parser `p` one or more times.

    A similar parser combinator `many(p)` means apply `p` zero or more times, whereas
    `oneplus(p)` means apply `p` one or more times.

    Examples:

    ```pycon
    >>> expr = oneplus(a("x"))
    >>> expr.parse("x")
    ['x']
    >>> expr.parse("xx")
    ['x', 'x']
    >>> expr.parse("y")
    Traceback (most recent call last):
        ...
    parser.NoParseError: got unexpected token: 'y', expected: 'x'

    ```
    """

    @Parser
    def _oneplus(tokens: Sequence[_A], s: State) -> Tuple[List[_B], State]:
        (v1, s2) = p.run(tokens, s)
        (v2, s3) = many(p).run(tokens, s2)
        return [v1] + v2, s3

    _oneplus.name = "(%s, { %s })" % (p.name, p.name)
    return _oneplus


def with_forward_decls(suspension: Callable[[], Parser[_A, _B]]) -> Parser[_A, _B]:
    warnings.warn(
        "Use forward_decl() instead:\n"
        "\n"
        "    p = forward_decl()\n"
        "    ...\n"
        "    p.define(parser_value)\n",
        DeprecationWarning,
    )

    @Parser
    def f(tokens: Sequence[_A], s: State) -> Tuple[_B, State]:
        return suspension().run(tokens, s)

    return f


def forward_decl() -> Parser[Any, Any]:
    """Return an undefined parser that can be used as a forward declaration.

    Type: `Parser[Any, Any]`

    Use `p = forward_decl()` in combination with `p.define(...)` to define recursive
    parsers.


    Examples:

    ```pycon
    >>> expr = forward_decl()
    >>> expr.define(a("x") + maybe(expr) + a("y"))
    >>> expr.parse("xxyy")  # noqa
    ('x', ('x', None, 'y'), 'y')
    >>> expr.parse("xxy")
    Traceback (most recent call last):
        ...
    parser.NoParseError: got unexpected end of input, expected: 'y'

    ```

    !!! Note

        If you care about static types, you should add a type hint for your forward
        declaration, so that your type checker can check types in `p.define(...)` later:

        ```python
        p: Parser[str, int] = forward_decl()
        p.define(a("x"))  # Type checker error
        p.define(a("1") >> int)  # OK
        ```
    """

    @Parser
    def f(_tokens: Any, _s: Any) -> Any:
        raise NotImplementedError("you must define() a forward_decl somewhere")

    f.name = "forward_decl()"
    return f


if __name__ == "__main__":
    import doctest

    doctest.testmod()
