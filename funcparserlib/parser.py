# -*- coding: utf-8 -*-

# Copyright © 2009/2021 Andrey Vlasovskikh
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

"""Recursive descent parser library based on functional combinators.

Basic combinators are taken from the Harrison's book [Introduction to Functional
Programming][1] and translated from ML into Python.

  [1]: https://www.cl.cam.ac.uk/teaching/Lectures/funprog-jrh-1996/

A parser is represented by a function of type:

    def run(tokens: Sequence[A], s: State) -> Tuple[B, State]: ...

that takes as its input a sequence of tokens of arbitrary type `A` and a current
parsing state and returns a pair of the parsed value of arbitrary type `B` and the new
parsing state.

The parsing state includes the current position in the sequence being parsed, and the
position of the rightmost token that has been consumed while parsing for better error
messages.

Parser functions are wrapped into objects of the class `Parser[A, B]`. This class
implements custom operators `+` for sequential composition of parsers, `|` for choice
composition, `>>` for transforming the result of parsing. The method `Parser.parse()`
provides an easier way to parse tokens by hiding the details related to the parser
state:

    class Parser(Generic[A, B]):
        def parse(self, tokens: Sequence[A]) -> B: ...

Although this module is able to deal with sequences of any objects, the recommended
way of using it is parsing `Sequence[Token]`. `Token` objects are produced by a
regexp-based tokenizer defined in `funcparserlib.lexer`. By using it this way you get
more readable parsing error messages (as `Token` objects contain their position in the
source file) and good separation of lexical and syntactic levels of the grammar.
See the examples in docs and tests for more info.

Debug messages are emitted via a `logging.Logger` object named `"funcparserlib"`.
"""

from __future__ import unicode_literals

__all__ = [
    "some",
    "a",
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

log = logging.getLogger("funcparserlib")

debug = False


class Parser(object):
    """Wrapper for a parser function with several methods for composing parsers."""

    def __init__(self, p):
        """Wrap the parser function `p` into a `Parser` object."""
        self.name = ""
        self.define(p)

    def named(self, name):
        """Specify the name of the parser for a more readable parsing log."""
        self.name = name
        return self

    def define(self, p):
        """Define a parser to be wrapped into this object.

        Should be used only with `forward_decl()` parsers to define them later.
        """
        f = getattr(p, "run", p)
        if debug:
            setattr(self, "_run", f)
        else:
            setattr(self, "run", f)
        self.named(getattr(p, "name", p.__doc__))

    def run(self, tokens, s):
        """Run the parser function against the tokens using the specified parsing
        state."""
        if debug:
            log.debug("trying %s" % self.name)
        return self._run(tokens, s)  # noqa

    def _run(self, tokens, s):
        raise NotImplementedError("you must define() a parser")

    def parse(self, tokens):
        """Parse the sequence of tokens and return the parsed value.

        It provides a way to invoke a parser with details about the parser state. Also,
        it makes error messages more readable by showing the position of the
        rightmost token that it has managed to reach.
        """
        try:
            (tree, _) = self.run(tokens, State())
            return tree
        except NoParseError as e:
            max = e.state.max
            if len(tokens) > max:
                tok = tokens[max]
            else:
                tok = "<EOF>"
            raise NoParseError("%s: %s" % (e.msg, tok), e.state)

    def __add__(self, other):
        """Sequential composition of parsers. It runs this parser, then the other
        parser.

        NOTE: The real type of the parsed value isn't always such as specified.
        Here we use dynamic typing for ignoring the tokens that are of no
        interest to the user. Also, we merge parsing results into a single `_Tuple`
        unless the user explicitly prevents it. See also `skip` and `>>` combinators.
        """

        def magic(v1, v2):
            vs = [v for v in [v1, v2] if not isinstance(v, _Ignored)]
            if len(vs) == 1:
                return vs[0]
            elif len(vs) == 2:
                if isinstance(vs[0], _Tuple):
                    return _Tuple(v1 + (v2,))
                else:
                    return _Tuple(vs)
            else:
                return _Ignored(())

        @Parser
        def _add(tokens, s):
            (v1, s2) = self.run(tokens, s)
            (v2, s3) = other.run(tokens, s2)
            return magic(v1, v2), s3

        # or in terms of bind and pure:
        # _add = self.bind(lambda x: other.bind(lambda y: pure(magic(x, y))))
        _add.name = "(%s , %s)" % (self.name, other.name)
        return _add

    def __or__(self, other):
        """Choice composition of parsers. It runs this parser and returns its result. If
        the parser fails, it runs the other parser."""

        @Parser
        def _or(tokens, s):
            try:
                return self.run(tokens, s)
            except NoParseError as e:
                return other.run(tokens, State(s.pos, e.state.max))

        _or.name = "(%s | %s)" % (self.name, other.name)
        return _or

    def __rshift__(self, f):
        """Given a function from `B` to `C`, transforms a parser of `B` into a parser of
        `C`. It is useful for transforming the parsed value into another value before
        including it into the parse tree (the AST).

        You can think of this combinator as a functor from `(B) -> C` to
        `(Parser[A, B]) -> Parser[A, C]`. It is also known as `map` in other areas.
        """

        @Parser
        def _shift(tokens, s):
            (v, s2) = self.run(tokens, s)
            return f(v), s2

        # or in terms of bind and pure:
        # _shift = self.bind(lambda x: pure(f(x)))
        _shift.name = "(%s)" % (self.name,)
        return _shift

    def bind(self, f):
        """Monadic bind method.

        It may be used internally to implement other combinators. Functions `bind` and
        `pure` make the `Parser` a monad.

        You can parse any context-free grammar without resorting to `bind`. Due to its
        poor performance please use it only when you really need it.
        """

        @Parser
        def _bind(tokens, s):
            (v, s2) = self.run(tokens, s)
            return f(v).run(tokens, s2)

        _bind.name = "(%s >>=)" % (self.name,)
        return _bind


class State(object):
    """Parsing state that is maintained basically for error reporting.

    It consists of the current position `pos` in the sequence being parsed, and the
    position `max` of the rightmost token that has been consumed while parsing.
    """

    def __init__(self, pos=0, max=0):
        self.pos = pos
        self.max = max

    def __str__(self):
        return str((self.pos, self.max))

    def __repr__(self):
        return "State(%r, %r)" % (self.pos, self.max)


class NoParseError(Exception):
    def __init__(self, msg="", state=None):
        self.msg = msg
        self.state = state

    def __str__(self):
        return self.msg


class _Tuple(tuple):
    pass


class _Ignored(object):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return "_Ignored(%s)" % repr(self.value)


@Parser
def finished(tokens, s):
    """Throw an exception if there are any unparsed tokens in the sequence."""
    if s.pos >= len(tokens):
        return None, s
    else:
        raise NoParseError("should have reached <EOF>", s)


finished.name = "finished"


def many(p):
    """Apply parser `p` as many times as it succeeds.

    Return a parser that infinitely applies the parser `p` to the input sequence
    of tokens while it successfully parses them. The returned parser returns a
    list of parsed values.
    """

    @Parser
    def _many(tokens, s):
        res = []
        try:
            while True:
                (v, s) = p.run(tokens, s)
                res.append(v)
        except NoParseError as e:
            return res, State(s.pos, e.state.max)

    _many.name = "{ %s }" % p.name
    return _many


def some(pred):
    """Return a parser that parses a token if it satisfies the predicate `pred`."""

    @Parser
    def _some(tokens, s):
        if s.pos >= len(tokens):
            raise NoParseError("no tokens left in the stream", s)
        else:
            t = tokens[s.pos]
            if pred(t):
                pos = s.pos + 1
                s2 = State(pos, max(pos, s.max))
                if debug:
                    log.debug('*matched* "%s", new state = %s' % (t, s2))
                return t, s2
            else:
                if debug:
                    log.debug('failed "%s", state = %s' % (t, s))
                raise NoParseError("got unexpected token", s)

    _some.name = "(some)"
    return _some


def a(value):
    """Return a parser that parses a token if it's equal to `value`."""
    name = getattr(value, "name", value)
    return some(lambda t: t == value).named('(a "%s")' % (name,))


def pure(x):
    @Parser
    def _pure(_, s):
        return x, s

    _pure.name = "(pure %r)" % (x,)
    return _pure


def maybe(p):
    """Return a parser that returns `None` if parsing fails."""
    return (p | pure(None)).named("[ %s ]" % (p.name,))


def skip(p):
    """Return a parser which results are ignored by the combinator `+`.

    This is useful for throwing away elements of concrete syntax (e.g. `","`, `";"`).

    You shouldn't pass the resulting parser to any combinators other than `+`.
    """
    return p >> _Ignored


def oneplus(p):
    """Return a parser that applies the parser `p` one or more times."""

    @Parser
    def _oneplus(tokens, s):
        (v1, s2) = p.run(tokens, s)
        (v2, s3) = many(p).run(tokens, s2)
        return [v1] + v2, s3

    _oneplus.name = "(%s , { %s })" % (p.name, p.name)
    return _oneplus


def with_forward_decls(suspension):
    """Return a parser that computes itself lazily as a result of the suspension
    provided.

    It is needed when some parsers contain forward references to parsers defined later
    and such references are cyclic. See examples for more details.

    This function is deprecated, use `forward_decl()` instead.
    """

    warnings.warn(
        "Use forward_decl() instead:\n"
        "\n"
        "    p = forward_decl()\n"
        "    ...\n"
        "    p.define(parser_value)\n",
        DeprecationWarning,
    )

    @Parser
    def f(tokens, s):
        return suspension().run(tokens, s)

    return f


def forward_decl():
    """Return an undefined parser that can be used as a forward declaration.

    You should define it via `p.define(parser_value)` when all the parsers it depends
    on are available.
    """

    @Parser
    def f(_tokens, _s):
        raise NotImplementedError("you must define() a forward_decl somewhere")

    return f


if __name__ == "__main__":
    import doctest

    doctest.testmod()
