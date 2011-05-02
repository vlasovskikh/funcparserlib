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

'''A recurisve descent parser library based on functional combinators.

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
'''

__all__ = [
    'some', 'a', 'many', 'fwd', 'eof', 'maybe', 'skip', 'oneplus', 'pure',
    'name_parser_vars', 'SyntaxError', 'ParserError',
]

from funcparserlib.util import SyntaxError

class ParserError(SyntaxError):
    '''User-visible parsing error.'''
    pass

class GrammarError(Exception):
    '''Raised when the grammar definition itself contains errors.'''
    pass

class NoParseError(Exception):
    '''Internal no-parse exception for backtracking.'''

    def __init__(self, msg='', state=None):
        self.msg = msg
        self.state = state

    def __unicode__(self):
        return self.msg

    def __str__(self):
        return self.msg.encode()

class Parser(object):
    '''A callable parser object that defines some operators for parser
    composition and the `parse()` function as its external interface.
    '''

    def parse(self, tokens):
        '''Applies the parser to the tokens producing a parsing result.

        It provides a way to invoke a parser hiding details related to the
        parser state. Also it makes error messages more readable by specifying
        the position of the rightmost token that has been reached.
        '''
        p = non_halting(self)
        if p:
            raise GrammarError("parser '%s' does not halt, please fix your "
                               'grammar; see the FAQ for details' % p)
        try:
            (tree, _) = self(tokens, State())
            return tree
        except NoParseError, e:
            max = e.state.max
            tok = tokens[max] if max < len(tokens) else '<EOF>'
            raise ParserError(u'%s: %s' % (e.msg, tok),
                              getattr(tok, 'pos', None))

    def __call__(self, tokens, s):
        return GrammarError('an abstract parser cannot be called')

    def __add__(self, other):
        '''A sequential composition of parsers.

        The resulting parser merges the parsed sequence into a single `_Tuple`
        unless the user explicitely prevents it. See also `skip()` and `>>`
        combinators.
        '''
        return _Seq(self, other)

    def __or__(self, other):
        '''A choice composition of two parsers.'''
        return _Alt(self, other)

    def __rshift__(self, f):
        '''An interpreting parser.

        Given a function from `b` to `c`, transforms a parser of `b` into a
        parser of `c`. It is useful for transorming a parser value into another
        value for making it a part of a parse tree or an AST.
        '''
        return _Map(self, f)

    def __str__(self):
        return getattr(self, 'name', self.ebnf())

    def named(self, name):
        'Specifies the name of the parser.'
        self.name = name
        return self

    def ebnf(self):
        'The EBNF grammar expression for the parser.'
        return GrammarError('no EBNF expression for an abstract parser')

class _Map(Parser):
    '''An interpreting parser.'''

    def __init__(self, p, f):
        self.p = p
        self.f = f

    def __call__(self, tokens, s):
        (v, s2) = self.p(tokens, s)
        return (self.f(v), s2)

    def ebnf(self):
        return str(self.p)

class _Seq(Parser):
    '''A sequential composition of parsers.'''

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
        vs = []
        for p in self.ps:
            (v, s) = p(tokens, s)
            vs.append(v)
        return (reduce(magic, vs), s)

    def ebnf(self):
        return ', '.join(ebnf_brackets(str(x)) for x in self.ps)

class _Alt(Parser):
    '''A choice composition of parsers.'''

    def __init__(self, p1, p2):
        if isinstance(p1, _Alt):
            self.ps = p1.ps + [p2]
        else:
            self.ps = [p1, p2]

    def __call__(self, tokens, s):
        e = NoParseError('no error', s)
        for p in self.ps:
            try:
                return p(tokens, s)
            except NoParseError, npe:
                e = npe
                s = State(s.pos, e.state.max)
                continue
        raise e

    def ebnf(self):
        return ' | '.join(ebnf_brackets(str(x)) for x in self.ps)

class _Fwd(Parser):
    '''An undefined parser that can be used as a forward declaration.

    You will be able to `define()` it when all the parsers it depends on are
    available.
    '''

    def __init__(self):
        self.p = None

    def define(self, p):
        self.p = p

    def __call__(self, tokens, s):
        if self.p:
            return self.p(tokens, s)
        else:
            raise NotImplementedError('you must define() a fwd')

    def __str__(self):
        return getattr(self, 'name', 'id%d' % id(self))

    def ebnf(self):
        return str(self.p)

class _Eof(Parser):
    '''Throws an exception if any tokens are left in the input unparsed.'''

    def __call__(self, tokens, s):
        if s.pos >= len(tokens):
            return (None, s)
        else:
            raise NoParseError('<EOF> not found', s)

    def ebnf(self):
        return '? eof ?'

class _Many(Parser):
    '''A parser that infinitely applies the parser `p` to the input sequence of
    tokens while it successfully parsers them. It returns a list of parsed
    values.
    '''

    def __init__(self, p):
        self.p = p

    def __call__(self, tokens, s):
        # Iterative implementation preventing the stack overflow
        res = []
        try:
            while True:
                (v, s) = self.p(tokens, s)
                res.append(v)
        except NoParseError, e:
            return (res, e.state)

    def ebnf(self):
        return '{ %s }' % self.p

class _Pure(Parser):
    '''A pure parser that returns its result without looking at the input.'''

    def __init__(self, x):
        self.x = x

    def __call__(self, tokens, s):
        return (self.x, s)

    def ebnf(self):
        return '? pure(%s) ?' % (self.x,)

# Deprecated
class _Some(Parser):
    '''A parser that parses a token if it satisfies a predicate `pred`.'''

    def __init__(self, pred):
        self.pred = pred

    def __call__(self, tokens, s):
        try:
            t = tokens[s.pos]
        except IndexError:
            raise NoParseError('no tokens left in the stream', s)
        if self.pred(t):
            pos = s.pos + 1
            s2 = State(pos, max(pos, s.max))
            return (t, s2)
        else:
            raise NoParseError('got unexpected token', s)

    def ebnf(self):
        return '? some() ?'

class State(object):
    '''A parsing state that is maintained basically for error reporting.

    It consists of the current position `pos` in the sequence being parsed and
    the position `max` of the rightmost token that has been consumed while
    parsing.
    '''
    def __init__(self, pos=0, max=0):
        self.pos = pos
        self.max = max

    def __unicode__(self):
        return unicode((self.pos, self.max))

    def __repr__(self):
        return 'State(%r, %r)' % (self.pos, self.max)

class _Tuple(tuple): pass

class _Ignored(object):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return '_Ignored(%r)' % (self.value,)

def a(value):
    '''Returns a parser that parses a token that is equal to the value.'''
    name = getattr(value, 'name', value)
    p = some(lambda t: t == value)
    p.ebnf = lambda: '"%s"' % name
    return p

def maybe(p):
    '''Returns a parser that retuns `None` if parsing fails.'''
    q = p | pure(None)
    q.ebnf = lambda: '[ %s ]' % p
    return q

def skip(p):
    '''Returns a parser such that its results are ignored by the combinator `+`.

    It is useful for throwing away elements of concrete syntax (e. g. ",", ";").
    '''
    return p >> _Ignored

def oneplus(p):
    '''Returns a parser that applies the parser `p` one or more times.'''
    return p + many(p) >> (lambda x: [x[0]] + x[1])

def name_parser_vars(vars):
    '''Name parsers after their variables.

    Named parsers are nice for debugging and error reporting.

    The typical usage is to define all the parsers of the grammar in the same
    scope and run `name_parser_vars(locals())` to name them all instead of calling
    `Parser.named()` manually for each parser.
    '''
    for k, v in vars.items():
        if isinstance(v, Parser):
            v.named(k)

def non_halting(p):
    '''Returns a non-halting part of parser `p` or `None`.'''
    return left_recursive(p) or non_halting_many(p)

def left_recursive(p, fwds=[], seqs=[]):
    '''Returns a left-recursive part of parser `p` or `None`.'''
    if isinstance(p, (_Map, _Many)):
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
            return (left_recursive(p.ps[0], fwds, seqs) or
                    any(left_recursive(x, [], [p] + seqs) for x in p.ps[1:]))
    elif isinstance(p, _Alt):
        return any(left_recursive(x, fwds, seqs) for x in p.ps)
    else:
        return None

def non_halting_many(p, fwds=[]):
    '''Returns a non-halting `many()` part of parser `p` or `None`.'''
    if isinstance(p, _Map):
        return non_halting_many(p.p, fwds)
    elif isinstance(p, _Fwd):
        if p in fwds:
            return None
        else:
            return non_halting_many(p.p, [p] + fwds)
    elif isinstance(p, (_Seq, _Alt)):
        return any(non_halting_many(x, fwds) for x in p.ps)
    elif isinstance(p, _Many):
        return p if not makes_progress(p.p) else None
    else:
        return None

def makes_progress(p, fwds=[]):
    '''Returns `True` if parser `p` must consume one or more tokens in order to
    succeed.
    '''
    if isinstance(p, _Map):
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
    elif isinstance(p, (_Some, _Eof)):
        return True
    else:
        return False

def ebnf_grammar(p):
    'The EBNF grammar for the parser `p` as the top-level symbol.'
    def ebnf_rules(p, ps):
        if p in ps:
            return [], ps
        ps = [p] + ps
        if isinstance(p, (_Map, _Fwd, _Many)):
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
    return '\n'.join(reversed(rs))

def ebnf_rule(p):
    'The EBNF grammar rule for the parser `p`.'
    return '%s = %s;' % (getattr(p, 'name', 'id%d' % id(p)),
                         p.ebnf())

def ebnf_brackets(s):
    return (s if ' ' not in s or
                 any(s.startswith(x) for x in '{[(?')
              else '(%s)' % s)

# Aliases for exporting
eof = _Eof()
many = _Many
some = _Some
pure = _Pure
fwd = _Fwd

