# -*- coding: utf-8 -*-

# Copyright (c) 2008/2013 Andrey Vlasovskikh
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""A recurisve descent parser library based on functional combinators.

Basic combinators are taken from Harrison's book ["Introduction to Functional
Programming"][1] and translated from ML into Python. See also [a Russian
translation of the book][2].

  [1]: http://www.cl.cam.ac.uk/teaching/Lectures/funprog-jrh-1996/
  [2]: http://code.google.com/p/funprog-ru/

A parser `p` is represented by a function of type:

    p :: Sequence(a), State -> (b, State)

that takes as its input a sequence of tokens of arbitrary type `a` and a
current parsing state and return a pair of a parsed token of arbitrary type
`b` and the new parsing state.

The parsing state includes the current position in the sequence being parsed and
the position of the rightmost token that has been consumed while parsing.

Parser functions are wrapped into an object of the class `Parser`. This class
implements custom operators `+` for sequential composition of parsers, `|` for
choice composition, `>>` for transforming the result of parsing. The method
`Parser.parse` provides an easier way for invoking a parser hiding details
related to a parser state:

    Parser.parse :: Parser(a, b), Sequence(a) -> b

Altough this module is able to deal with a sequences of any kind of objects, the
recommended way of using it is applying a parser to a `Sequence(Token)`.
`Token` objects are produced by a regexp-based tokenizer defined in
`funcparserlib.lexer`. By using it this way you get more readable parsing error
messages (as `Token` objects contain their position in the source file) and good
separation of lexical and syntactic levels of the grammar. See examples for more
info.

Debug messages are emitted via a `logging.Logger` object named
`"funcparserlib"`.
"""

__all__ = [
    'some', 'a', 'many', 'pure', 'finished', 'maybe', 'skip', 'oneplus',
    'forward_decl', 'NoParseError',
]

import logging

log = logging.getLogger('funcparserlib')

debug = False


class Parser(object):
    """A wrapper around a parser function that defines some operators for parser
    composition.
    """

    def __init__(self, p):
        """Wraps a parser function p into an object."""
        self.define(p)

    def named(self, name):
        """Specifies the name of the parser for more readable parsing log."""
        self.name = name
        return self

    def define(self, p):
        """Defines a parser wrapped into this object."""
        f = getattr(p, 'run', p)
        if debug:
            setattr(self, '_run', f)
        else:
            setattr(self, 'run', f)
        self.named(getattr(p, 'name', p.__doc__))

    def run(self, tokens, s):
        """Sequence(a), State -> (b, State)

        Runs a parser wrapped into this object.
        """
        if debug:
            log.debug(u'trying %s' % self.name)
        return self._run(tokens, s)

    def _run(self, tokens, s):
        raise NotImplementedError(u'you must define() a parser')

    def parse(self, tokens):
        """Sequence(a) -> b

        Applies the parser to a sequence of tokens producing a parsing result.

        It provides a way to invoke a parser hiding details related to the
        parser state. Also it makes error messages more readable by specifying
        the position of the rightmost token that has been reached.
        """
        try:
            (tree, _) = self.run(tokens, State())
            return tree
        except NoParseError, e:
            max = e.state.max
            if len(tokens) > max:
                tok = tokens[max]
            else:
                tok = u'<EOF>'
            raise NoParseError(u'%s: %s' % (e.msg, tok), e.state)

    def __add__(self, other):
        """Parser(a, b), Parser(a, c) -> Parser(a, _Tuple(b, c))

        A sequential composition of parsers.

        NOTE: The real type of the parsed value isn't always such as specified.
        Here we use dynamic typing for ignoring the tokens that are of no
        interest to the user. Also we merge parsing results into a single _Tuple
        unless the user explicitely prevents it. See also skip and >>
        combinators.
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
        _add.name = u'(%s , %s)' % (self.name, other.name)
        return _add

    def __or__(self, other):
        """Parser(a, b), Parser(a, c) -> Parser(a, b or c)

        A choice composition of two parsers.

        NOTE: Here we are not providing the exact type of the result. In a
        statically typed langage something like Either b c could be used. See
        also + combinator.
        """

        @Parser
        def _or(tokens, s):
            try:
                return self.run(tokens, s)
            except NoParseError, e:
                return other.run(tokens, State(s.pos, e.state.max))

        _or.name = u'(%s | %s)' % (self.name, other.name)
        return _or

    def __rshift__(self, f):
        """Parser(a, b), (b -> c) -> Parser(a, c)

        Given a function from b to c, transforms a parser of b into a parser of
        c. It is useful for transorming a parser value into another value for
        making it a part of a parse tree or an AST.

        This combinator may be thought of as a functor from b -> c to Parser(a,
        b) -> Parser(a, c).
        """

        @Parser
        def _shift(tokens, s):
            (v, s2) = self.run(tokens, s)
            return f(v), s2

        # or in terms of bind and pure:
        # _shift = self.bind(lambda x: pure(f(x)))
        _shift.name = u'(%s)' % (self.name,)
        return _shift

    def bind(self, f):
        """Parser(a, b), (b -> Parser(a, c)) -> Parser(a, c)

        NOTE: A monadic bind function. It is used internally to implement other
        combinators. Functions bind and pure make the Parser a Monad.
        """

        @Parser
        def _bind(tokens, s):
            (v, s2) = self.run(tokens, s)
            return f(v).run(tokens, s2)

        _bind.name = u'(%s >>=)' % (self.name,)
        return _bind


class State(object):
    """A parsing state that is maintained basically for error reporting.

    It consists of the current position pos in the sequence being parsed and
    the position max of the rightmost token that has been consumed while
    parsing.
    """

    def __init__(self, pos=0, max=0):
        self.pos = pos
        self.max = max

    def __str__(self):
        return unicode((self.pos, self.max))

    def __repr__(self):
        return u'State(%r, %r)' % (self.pos, self.max)


class NoParseError(Exception):
    def __init__(self, msg=u'', state=None):
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
        return u'_Ignored(%s)' % repr(self.value)


@Parser
def finished(tokens, s):
    """Parser(a, None)

    Throws an exception if any tokens are left in the input unparsed.
    """
    if s.pos >= len(tokens):
        return None, s
    else:
        raise NoParseError(u'should have reached <EOF>', s)


finished.name = u'finished'


def many(p):
    """Parser(a, b) -> Parser(a, [b])

    Returns a parser that infinitely applies the parser p to the input sequence
    of tokens while it successfully parsers them. The resulting parser returns a
    list of parsed values.
    """

    @Parser
    def _many(tokens, s):
        """Iterative implementation preventing the stack overflow."""
        res = []
        try:
            while True:
                (v, s) = p.run(tokens, s)
                res.append(v)
        except NoParseError, e:
            return res, State(s.pos, e.state.max)

    _many.name = u'{ %s }' % p.name
    return _many


def some(pred):
    """(a -> bool) -> Parser(a, a)

    Returns a parser that parses a token if it satisfies a predicate pred.
    """

    @Parser
    def _some(tokens, s):
        if s.pos >= len(tokens):
            raise NoParseError(u'no tokens left in the stream', s)
        else:
            t = tokens[s.pos]
            if pred(t):
                pos = s.pos + 1
                s2 = State(pos, max(pos, s.max))
                if debug:
                    log.debug(u'*matched* "%s", new state = %s' % (t, s2))
                return t, s2
            else:
                if debug:
                    log.debug(u'failed "%s", state = %s' % (t, s))
                raise NoParseError(u'got unexpected token', s)

    _some.name = u'(some)'
    return _some


def a(value):
    """Eq(a) -> Parser(a, a)

    Returns a parser that parses a token that is equal to the value value.
    """
    name = getattr(value, 'name', value)
    return some(lambda t: t == value).named(u'(a "%s")' % (name,))


def pure(x):
    @Parser
    def _pure(_, s):
        return x, s

    _pure.name = u'(pure %r)' % (x,)
    return _pure


def maybe(p):
    """Parser(a, b) -> Parser(a, b or None)

    Returns a parser that retuns None if parsing fails.

    NOTE: In a statically typed language, the type Maybe b could be more
    approprieate.
    """
    return (p | pure(None)).named(u'[ %s ]' % (p.name,))


def skip(p):
    """Parser(a, b) -> Parser(a, _Ignored(b))

    Returns a parser which results are ignored by the combinator +. It is useful
    for throwing away elements of concrete syntax (e. g. ",", ";").
    """
    return p >> _Ignored


def oneplus(p):
    """Parser(a, b) -> Parser(a, [b])

    Returns a parser that applies the parser p one or more times.
    """
    q = p + many(p) >> (lambda x: [x[0]] + x[1])
    return q.named(u'(%s , { %s })' % (p.name, p.name))


def with_forward_decls(suspension):
    """(None -> Parser(a, b)) -> Parser(a, b)

    Returns a parser that computes itself lazily as a result of the suspension
    provided. It is needed when some parsers contain forward references to
    parsers defined later and such references are cyclic. See examples for more
    details.
    """

    @Parser
    def f(tokens, s):
        return suspension().run(tokens, s)

    return f


def forward_decl():
    """None -> Parser(?, ?)

    Returns an undefined parser that can be used as a forward declaration. You
    will be able to define() it when all the parsers it depends on are
    available.
    """

    @Parser
    def f(tokens, s):
        raise NotImplementedError(u'you must define() a forward_decl somewhere')

    return f


if __name__ == '__main__':
    import doctest
    doctest.testmod()
