# -*- coding: utf-8 -*-

import sys, os
from re import MULTILINE
from pprint import pformat
from funcparserlib.lexer import make_tokenizer, Token, LexerError
from funcparserlib.parser import (some, a, maybe, many, finished, skip,
    oneplus, NoParseError)
try:
    from collections import namedtuple
except ImportError:
    # Примитивная реализация namedtuple для 2.1 < Python < 2.6
    def namedtuple(name, fields):
        'Only space-delimited fields are supported.'
        def prop(i, name):
            return (name, property(lambda self: self[i]))
        methods = dict(prop(i, f) for i, f in enumerate(fields.split(' ')))
        methods.update({
            '__new__': lambda cls, *args: tuple.__new__(cls, args),
            '__repr__': lambda self: '%s(%s)' % (
                name,
                ', '.join('%s=%r' % (
                    f, getattr(self, f)) for f in fields.split(' ')))})
        return type(name, (tuple,), methods)

ENCODING = 'utf-8'

Graph = namedtuple('Graph', 'strict type id stmts')
Node = namedtuple('Node', 'id attrs')
Attr = namedtuple('Attr', 'name value')
Edge = namedtuple('Edge', 'id links attrs')

def tokenize(str):
    'str -> Sequence(Token)'
    specs = [
        ('Comment', (r'/\*(.|[\r\n])*?\*/', MULTILINE)),
        ('Comment', (r'//.*',)),
        ('NL',      (r'[\r\n]+',)),
        ('Space',   (r'[ \t\r\n]+',)),
        ('Name',    (r'[A-Za-z\200-\377_][A-Za-z\200-\377_0-9]*',)),
        ('Op',      (r'[{};,=\[\]]|(->)|(--)',)),
        ('Number',  (r'-?(\.[0-9]+)|([0-9]+(\.[0-9]*)?)',)),
        ('String',  (r'"[^"]*"',)), # '\"' escapes are ignored
    ]
    useless = ['Comment', 'NL', 'Space']
    t = make_tokenizer(specs)
    return [x for x in t(str) if x.type not in useless]

def parse(seq):
    '''Sequence(Token) -> object

    Based on [the DOT grammar][1].

      [1]: http://www.graphviz.org/doc/info/lang.html
    '''
    unarg = lambda f: lambda args: f(*args)
    tokval = lambda x: x.value
    flatten = lambda list: sum(list, [])
    n = lambda s: a(Token('Name', s)) >> tokval
    op = lambda s: a(Token('Op', s)) >> tokval
    id = some(lambda t: t.type in ['Name', 'Number', 'String']).named('id') >> tokval

    node_id = id # + maybe(port)
    a_list = (
        id +
        maybe(skip(op('=')) + id) +
        skip(maybe(op(',')))
        >> unarg(Attr))
    attr_list = (
        many(skip(op('[')) + many(a_list) + skip(op(']')))
        >> flatten).named('attr_list')
    node_stmt = (node_id + attr_list >> unarg(Node)).named('node_stmt')
    edge_rhs = skip(op('->') | op('--')) + node_id
    edge_stmt = (
        node_id +
        oneplus(edge_rhs) +
        attr_list
        >> unarg(Edge)).named('edge_stmt')
    stmt = (
        edge_stmt
        | node_stmt
        # | attr_stmt
        # | (id + op('=') + id)
        # | subgraph
    )
    stmt_list = many(stmt + skip(maybe(op(';'))))
    graph = (
        maybe(n('strict')) +
        maybe(n('graph') | n('digraph')) +
        maybe(id) +
        skip(op('{')) +
        stmt_list +
        skip(op('}'))
        >> unarg(Graph)).named('graph')
    dotfile = graph + skip(finished)

    return dotfile.parse(seq)

def main():
    #import logging
    #logging.basicConfig(level=logging.DEBUG)
    try:
        stdin = os.fdopen(sys.stdin.fileno(), 'rb')
        input = stdin.read().decode(ENCODING)
        tree = parse(tokenize(input))
        print pformat(tree)
    except (NoParseError, LexerError), e:
        msg = (u'syntax error: %s' % e).encode(ENCODING)
        print >> sys.stderr, msg
        sys.exit(1)

if __name__ == '__main__':
    main()

