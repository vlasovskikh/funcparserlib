# -*- coding: utf-8 -*-

# Copyright (c) 2008/2011 Andrey Vlasovskikh
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

"""A recurisve descent parsing library based on functional combinators.

Basic combinators are taken from Harrison's book ["Introduction to Functional
Programming"][1] and translated from ML into Python. See also [a Russian
translation of the book][2].

  [1]: http://www.cl.cam.ac.uk/teaching/Lectures/funprog-jrh-1996/
  [2]: http://code.google.com/p/funprog-ru/

"""


__all__ = [
    'a', 'tok', 'many', 'fwd', 'eof', 'maybe', 'skip', 'oneplus',
    'name_parser_vars', 'SyntaxError', 'ParserError', 'memoize',
]


from warnings import warn
import logging
from funcparserlib.lexer import Token
from funcparserlib.util import SyntaxError


log = logging.getLogger('funcparserlib')


if not hasattr(logging, 'statistics'):
    logging.statistics = {}
stats = logging.statistics.setdefault('funcparserlib',
                                      {'memoize': {}})


class ParserError(SyntaxError):
    """User-visible parsing error."""
    pass


class GrammarError(Exception):
    """Raised when the grammar definition itself contains errors."""
    pass


class _NoParseError(Exception):
    """Internal no-parse exception for backtracking."""

    def __init__(self, msg='', state=None):
        self.msg = msg
        self.state = state

    def __unicode__(self):
        return self.msg

    def __str__(self):
        return self.msg.encode()


class Parser(object):
    """Base class for various parsers.

    It defines some operators for parser composition and the `parse()` function
    as its external interface.
    """

    def parse(self, tokens):
        """Apply the parser to the tokens and produce the parsing result.

        It provides a way to invoke a parser hiding details related to the
        parser state. Also it makes error messages more readable by specifying
        the position of the rightmost token that has been reached.

        """
        p = left_recursive(self)
        if p:
            raise GrammarError("Parser '%s' does not halt, remove left "
                               "recursion from your grammar" %
                               ebnf_rule(p))
        p = non_halting_many(self)
        if p:
            raise GrammarError("Parser '%s' does not halt, because it "
                               "contains maybe() or many() inside many()" %
                               ebnf_rule(p))

        for q, opts in non_ll_1_parts(self):
            warn(u'The grammar has a non-LL(1) part that '
                 u'may slow down parsing:\n\n    %s\n\n'
                 u'Several alternatives here may start '
                 u'with the same token, '
                 u'possible starting tokens are:\n\n    %s\n\n'
                 u'In order to get linear parsing time add memoize() '
                 u'to the biggest common subtree of the '
                 u'alternatives or transform your grammar to LL(1).' %
                 (ebnf_rule(q), u', '.join(unicode(x) for x in opts)),
                 stacklevel=2)

        _clear_caches(self)

        try:
            tree, _ = self(tokens, _State())
            log.debug('stats: %r' % stats)
            return tree
        except _NoParseError, e:
            max = e.state.max
            tok = tokens[max] if max < len(tokens) else 'eof'
            raise ParserError(u'%s: %s' % (e.msg, tok),
                              getattr(tok, 'pos', None),
                              max)

    def __call__(self, tokens, s):
        return GrammarError('an abstract parser cannot be called')

    def __add__(self, other):
        """Return a sequential composition of parsers.

        The resulting parser merges the parsed sequence into a single `_Tuple`
        unless the user explicitely prevents it. See also `skip()` and `>>`
        combinators.
        """
        return _Seq(self, other)

    def __or__(self, other):
        """Return a choice composition of two parsers."""
        return _Alt(self, other)

    def __rshift__(self, f):
        """Return an interpreting parser.

        Given a function from `b` to `c`, transforms a parser of `b` into a
        parser of `c`. It is useful for transorming a parser value into another
        value for making it a part of a parse tree or an AST.
        """
        return _Map(self, f)

    def __unicode__(self):
        return getattr(self, 'name', self.ebnf())

    def named(self, name):
        """Specify the name of the parser."""
        self.name = name
        return self

    def ebnf(self):
        """Get the EBNF grammar expression for the parser."""
        return GrammarError('no EBNF expression for an abstract parser')


class _Map(Parser):
    """Interpreting parser."""

    def __init__(self, p, f):
        self.p = p
        self.f = f

    def __call__(self, tokens, s):
        v, s2 = self.p(tokens, s)
        return self.f(v), s2

    def ebnf(self):
        return unicode(self.p)


class _Seq(Parser):
    """Sequential composition of parsers."""

    def __init__(self, p1, p2):
        if isinstance(p1, _Seq):
            self.ps = p1.ps + [p2]
        else:
            self.ps = [p1, p2]

    def __call__(self, tokens, s):
        def magic(v1, v2):
            vs = [v for v in [v1, v2] if not isinstance(v, _Ignored)]
            length = len(vs)
            if length == 1:
                return vs[0]
            elif length == 2:
                if isinstance(vs[0], _Tuple):
                    return _Tuple(v1 + (v2,))
                else:
                    return _Tuple(vs)
            else:
                return _Ignored(())
        p, ps = self.ps[0], self.ps[1:]
        res, s = p(tokens, s)
        for p in ps:
            v, s = p(tokens, s)
            res = magic(res, v)
        return res, s

    def ebnf(self):
        return u', '.join(ebnf_brackets(unicode(x)) for x in self.ps)


class _Alt(Parser):
    """Choice composition of parsers."""

    def __init__(self, p1, p2):
        if isinstance(p1, _Alt):
            self.ps = p1.ps + [p2]
        else:
            self.ps = [p1, p2]
        self.toks = None

    def __call__(self, tokens, s):
        if self.toks is None:
            self.toks = []
            try:
                tss = [first(p) for p in self.ps]
                if all(_MEMOIZE not in ts and
                       len(ts) == len(set(ts)) for ts in tss):
                    self.toks = [(t, p)
                                 for p, ts in zip(self.ps, tss)
                                 for t in ts]
            except GrammarError:
                pass
        # If there is only 1 possible token for each of the alternatives, then
        # optimize the parser lookup
        if self.toks:
            try:
                t = tokens[s.pos]
            except IndexError:
                raise _NoParseError('no tokens left in the stream', s)
            for tok, p in self.toks:
                if t == tok:
                    return p(tokens, s)
            for tok, p in self.toks:
                if tok ==_EPSYLON:
                    return p(tokens, s)
            raise _NoParseError('got unexpected token', s)
        else:
            e = _NoParseError('no error', s)
            for p in self.ps:
                try:
                    return p(tokens, s)
                except _NoParseError, npe:
                    e = npe
                    s = _State(s.pos, e.state.max)
                    continue
            raise e

    def ebnf(self):
        return u' | '.join(ebnf_brackets(unicode(x)) for x in self.ps)


class _Fwd(Parser):
    """Undefined parser that can be used as a forward declaration.

    You will be able to `define()` it when all the parsers it depends on are
    available.
    """

    def __init__(self):
        self.p = None

    def define(self, p):
        self.p = p

    def __call__(self, tokens, s):
        if self.p:
            return self.p(tokens, s)
        else:
            raise NotImplementedError('you must define() a fwd')

    def __unicode__(self):
        return getattr(self, 'name', u'id%d' % id(self))

    def ebnf(self):
        return unicode(self.p)


class _Eof(Parser):
    """Throws an exception if any tokens are left in the input unparsed."""

    def __call__(self, tokens, s):
        if s.pos >= len(tokens):
            return None, s
        else:
            raise _NoParseError('eof not found', s)

    def ebnf(self):
        return u'? eof ?'


class _Many(Parser):
    """Repeated application of a parser.

    A parser that infinitely applies the parser `p` to the input sequence of
    tokens while it successfully parsers them. It returns a list of parsed
    values.
    """

    def __init__(self, p):
        self.p = p

    def __call__(self, tokens, s):
        # Iterative implementation preventing the stack overflow
        res = []
        try:
            while True:
                v, s = self.p(tokens, s)
                res.append(v)
        except _NoParseError, e:
            return res, _State(s.pos, e.state.max)

    def ebnf(self):
        return u'{ %s }' % self.p


class _Pure(Parser):
    """Pure parser that returns its result without looking at the input."""

    def __init__(self, x):
        self.x = x

    def __call__(self, tokens, s):
        return self.x, s

    def ebnf(self):
        return u'? pure(%s) ?' % (self.x,)


class _Tok(Parser):
    """Parses a token equal to the specified token."""

    def __init__(self, token):
        self.tok = token

    def __call__(self, tokens, s):
        try:
            t = tokens[s.pos]
        except IndexError:
            raise _NoParseError('no tokens left in the stream', s)
        if t == self.tok:
            pos = s.pos + 1
            s2 = _State(pos, max(pos, s.max))
            return t, s2
        else:
            raise _NoParseError('got unexpected token', s)

    def ebnf(self):
        try:
            return self.tok.ebnf()
        except AttributeError:
            return u'? %s ?' % self.tok


def tok(type, value=None):
    return _Tok(Token(type, value))


class _Memoize(Parser):
    def __init__(self, p):
        self.p = p
        self.cache = {}
        self.stats = stats['memoize'][self] = {'hits': 0, 'misses': 0}

    def __getattr__(self, name):
        return getattr(self.p, name)

    def __call__(self, tokens, s):
        cache = self.cache
        try:
            res = cache[s.pos]
            self.stats['hits'] += 1
        except KeyError:
            res = self.p(tokens, s)
            cache[s.pos] = res
            self.stats['misses'] += 1
        return res

    def ebnf(self):
        return unicode(self.p)


def _clear_caches(p):
    for x in all_parsers(p):
        if isinstance(x, _Memoize):
            x.cache = {}


class _State(object):
    """Parsing state that is maintained mainly for error reporting.

    It consists of the current position `pos` in the sequence being parsed and
    the position `max` of the rightmost token that has been consumed while
    parsing.
    """
    def __init__(self, pos=0, max=0):
        self.pos = pos
        self.max = max

    def __unicode__(self):
        return unicode((self.pos, self.max))

    def __repr__(self):
        return '_State(%r, %r)' % (self.pos, self.max)


class _Tuple(tuple): pass


class _Ignored(object):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return '_Ignored(%r)' % (self.value,)


def maybe(p):
    """Return a parser that retuns `None` if parsing fails."""
    q = p | pure(None)
    q.ebnf = lambda: u'[ %s ]' % p
    return q


def skip(p):
    """Return a parser such that its results are ignored by the combinator `+`.

    It is useful for throwing away elements of concrete syntax (e. g. ",", ";").
    """
    return p >> _Ignored


def oneplus(p):
    """Return a parser that applies the parser `p` one or more times."""
    return p + many(p) >> (lambda x: [x[0]] + x[1])


def name_parser_vars(vars):
    """Name parsers after their variables.

    Named parsers are nice for debugging and error reporting.

    The typical usage is to define all the parsers of the grammar in the same
    scope and run `name_parser_vars(locals())` to name them all instead of calling
    `Parser.named()` manually for each parser.
    """
    for k, v in vars.items():
        if isinstance(v, Parser):
            v.named(k)


def non_halting(p):
    """Return a non-halting part of parser `p` or `None`."""
    return left_recursive(p) or non_halting_many(p)


def takewhile_included(pred, seq):
    last = False
    for x in seq:
        if last:
            return
        elif pred(x):
            yield x
        else:
            last = True
            yield x


def left_recursive(p, fwds=[], seqs=[]):
    """Return a left-recursive part of parser `p` or `None`."""
    def any_(xs):
        for x in xs:
            if x:
                return x
        return None

    if isinstance(p, (_Map, _Many, _Memoize)):
        return left_recursive(p.p, fwds, seqs)
    elif isinstance(p, _Fwd):
        if p in fwds:
            return p
        else:
            return left_recursive(p.p, [p] + fwds, seqs)
    elif isinstance(p, _Seq):
        if p in seqs:
            return None
        else:
            left = list(takewhile_included(lambda x: not makes_progress(x),
                                            p.ps))
            right = p.ps[len(left):]
            return (any_(left_recursive(x, fwds, seqs) for x in left) or
                    any_(left_recursive(x, [], [p] + seqs) for x in right))
    elif isinstance(p, _Alt):
        return any_(left_recursive(x, fwds, seqs) for x in p.ps)
    else:
        return None


def non_halting_many(p):
    """Return a non-halting `many()` part of parser `p` or `None`."""
    rs = [x for x in all_parsers(p) if isinstance(x, _Many) and
                                       not makes_progress(x.p)]
    return rs[0] if len(rs) > 0 else None


def makes_progress(p, fwds=[]):
    """Assert that the parser must consume some tokens in order to succeed."""
    if isinstance(p, (_Map, _Memoize)):
        return makes_progress(p.p, fwds)
    elif isinstance(p, _Fwd):
        if p in fwds:
            return False
        else:
            return makes_progress(p.p, [p] + fwds)
    elif isinstance(p, _Seq):
        return any(makes_progress(x, fwds) for x in p.ps)
    elif isinstance(p, _Alt):
        return all(makes_progress(x, fwds) for x in p.ps)
    elif isinstance(p, (_Eof, _Tok)):
        return True
    else:
        return False


def ebnf_grammar(p):
    """The EBNF grammar for the parser `p` as the top-level symbol."""
    def ebnf_rules(p, ps):
        if p in ps:
            return [], ps
        ps = [p] + ps
        if isinstance(p, (_Map, _Fwd, _Many, _Memoize)):
            rs, ps = ebnf_rules(p.p, ps)
        elif isinstance(p, (_Seq, _Alt)):
            rs = []
            for x in reversed(p.ps):
                new_rs, ps = ebnf_rules(x, ps)
                rs.extend(new_rs)
        else:
            rs = []
        if hasattr(p, 'name'):
            rs.append(ebnf_rule(p))
        return rs, ps
    rs, ps = ebnf_rules(p, [])
    return u'\n'.join(reversed(rs))


def ebnf_rule(p):
    return u'%s = %s;' % (getattr(p, 'name', u'id%d' % id(p)),
                          p.ebnf())


def ebnf_brackets(s):
    return (s if u' ' not in s or
                 any(s.startswith(x) for x in u'{[(?')
              else u'(%s)' % s)


def non_ll_1_parts(p):
    assert not non_halting(p)
    ps = dict((x, [t for t in first(x)
                     if t != _MEMOIZE])
              for x in all_parsers(p)
              if isinstance(x, _Alt))
    return [(k, v) for k, v in ps.items()
                   if len(v) != len(set(v))]


def all_parsers(p):
    def rec(p, fwds=[]):
        if isinstance(p, (_Seq, _Alt)):
            return sum([rec(x, fwds) for x in p.ps], [p])
        elif isinstance(p, (_Many, _Map, _Memoize)):
            return [p] + rec(p.p, fwds)
        elif isinstance(p, _Fwd):
            if p in fwds:
                return []
            else:
                return [p] + rec(p.p, [p] + fwds)
        else:
            return [p]
    return list(set(rec(p)))


def _symbol(s):
    return u'symbol', s


_EPSYLON = _symbol(u'epsylon')
_MEMOIZE = _symbol(u'memoize')


def first(p):
    if isinstance(p, _Tok):
        return [p.tok]
    elif isinstance(p, _Seq):
        res = []
        last_epsylon = False
        for x in p.ps:
            toks = first(x)
            res.extend(t for t in toks if t != _EPSYLON)
            last_epsylon = _EPSYLON in toks
            if not last_epsylon:
                break
        if last_epsylon:
            res.append(_EPSYLON)
        return res
    elif isinstance(p, _Alt):
        return sum([first(x) for x in p.ps], [])
    elif isinstance(p, (_Map, _Fwd)):
        return first(p.p)
    elif isinstance(p, _Many):
        return first(p.p) + [_EPSYLON]
    elif isinstance(p, _Pure):
        return [_EPSYLON]
    elif isinstance(p, _Eof):
        return []
    elif isinstance(p, _Memoize):
        return [_MEMOIZE]
    else:
        raise GrammarError('cannot analyse parser %s' % ebnf_rule(p))


# Aliases for exporting
eof = _Eof()
a = _Tok
many = _Many
pure = _Pure
fwd = _Fwd
memoize = _Memoize

